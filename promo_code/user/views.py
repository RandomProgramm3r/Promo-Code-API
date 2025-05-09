import django.db.models
import django.utils.timezone
import rest_framework.generics
import rest_framework.permissions
import rest_framework.response
import rest_framework.status
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import business.constants
import business.models
import user.pagination
import user.serializers


class UserSignUpView(
    rest_framework.generics.CreateAPIView,
):
    serializer_class = user.serializers.SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version

        access_token = refresh.access_token

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )


class UserSignInView(
    rest_framework_simplejwt.views.TokenObtainPairView,
):
    serializer_class = user.serializers.SignInSerializer


class UserProfileView(
    rest_framework.generics.RetrieveUpdateAPIView,
):
    """
    Retrieve (GET) and partially update (PATCH)
    detailed user profile information.
    """

    http_method_names = ['get', 'patch', 'options', 'head']
    serializer_class = user.serializers.UserProfileSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class UserPromoDetailView(rest_framework.generics.RetrieveAPIView):
    """
    Retrieve (GET) information about the promo without receiving a promo code.
    """

    queryset = (
        business.models.Promo.objects.select_related('company')
        .prefetch_related(
            'unique_codes',
        )
        .only(
            'id',
            'company__id',
            'company__name',
            'description',
            'image_url',
            'active',
            'active_from',
            'active_until',
            'mode',
            'used_count',
        )
    )

    serializer_class = user.serializers.UserPromoDetailSerializer

    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
    ]

    lookup_field = 'id'


class UserFeedView(rest_framework.generics.ListAPIView):
    serializer_class = user.serializers.PromoFeedSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated]
    pagination_class = user.pagination.UserFeedPagination

    def get_queryset(self):
        user = self.request.user
        user_age = user.other.get('age')
        user_country_raw = user.other.get('country')
        user_country = user_country_raw.lower() if user_country_raw else None

        queryset = business.models.Promo.objects.select_related('company')

        today_utc = django.utils.timezone.now().date()

        q_active_time = (
            django.db.models.Q(active_from__lte=today_utc)
            | django.db.models.Q(active_from__isnull=True)
        ) & (
            django.db.models.Q(active_until__gte=today_utc)
            | django.db.models.Q(active_until__isnull=True)
        )

        q_common_active = django.db.models.Q(
            mode=business.constants.PROMO_MODE_COMMON,
            used_count__lt=django.db.models.F('max_count'),
        )

        has_available_unique_codes = business.models.PromoCode.objects.filter(
            promo=django.db.models.OuterRef('pk'),
            is_used=False,
        )

        queryset = queryset.annotate(
            _has_available_unique_codes=django.db.models.Exists(
                has_available_unique_codes,
            ),
        )
        q_unique_active = django.db.models.Q(
            mode=business.constants.PROMO_MODE_UNIQUE,
            _has_available_unique_codes=True,
        )

        q_is_active_by_rules = q_active_time & (
            q_common_active | q_unique_active
        )

        q_target_empty = django.db.models.Q(target={})

        q_country_target_matches = django.db.models.Q()
        if user_country:
            q_country_target_matches = django.db.models.Q(
                target__country__iexact=user_country,
            )

        q_country_target_not_set_or_empty = (
            ~django.db.models.Q(target__has_key='country')
            | django.db.models.Q(target__country__isnull=True)
        )
        q_user_meets_country_target = (
            q_country_target_matches | q_country_target_not_set_or_empty
        )

        q_age_target_not_set = ~django.db.models.Q(
            target__has_key='age_from',
        ) & ~django.db.models.Q(target__has_key='age_until')
        q_user_meets_age_target = q_age_target_not_set

        if user_age is not None:
            q_age_from_ok = (
                ~django.db.models.Q(target__has_key='age_from')
                | django.db.models.Q(target__age_from__isnull=True)
                | django.db.models.Q(target__age_from__lte=user_age)
            )
            q_age_until_ok = (
                ~django.db.models.Q(target__has_key='age_until')
                | django.db.models.Q(target__age_until__isnull=True)
                | django.db.models.Q(target__age_until__gte=user_age)
            )
            q_user_age_in_defined_range = q_age_from_ok & q_age_until_ok
            q_user_meets_age_target = (
                q_age_target_not_set | q_user_age_in_defined_range
            )

        q_user_is_targeted = q_target_empty | (
            q_user_meets_country_target & q_user_meets_age_target
        )

        queryset = queryset.filter(q_user_is_targeted)

        active_param_str = self.request.query_params.get('active')
        if active_param_str is not None:
            active_param_bool = active_param_str.lower() == 'true'
            if active_param_bool:
                queryset = queryset.filter(q_is_active_by_rules)
            else:
                queryset = queryset.exclude(q_is_active_by_rules)

        return queryset.order_by('-created_at')

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        category_param = self.request.query_params.get('category')
        if category_param:
            category_param = category_param.lower()
        if category_param:
            filtered_pks = []
            for promo in queryset:
                target_categories = promo.target.get('categories')
                if not isinstance(target_categories, list):
                    continue
                if any(
                    cat_name.lower() == category_param
                    for cat_name in target_categories
                ):
                    filtered_pks.append(promo.pk)
            queryset = queryset.filter(pk__in=filtered_pks)
        return queryset

    def list(self, request, *args, **kwargs):
        query_serializer = user.serializers.UserFeedQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)
        self.validated_query_params = query_serializer.validated_data

        return super().list(request, *args, **kwargs)
