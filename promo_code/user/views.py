import django.db.models
import django.db.transaction
import django.shortcuts
import rest_framework.generics
import rest_framework.permissions
import rest_framework.response
import rest_framework.status
import rest_framework.views
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import business.models
import core.pagination
import user.models
import user.permissions
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

    queryset = business.models.Promo.objects.select_related('company').only(
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
        'like_count',
        'comment_count',
    )

    serializer_class = user.serializers.UserPromoDetailSerializer

    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
    ]

    lookup_field = 'id'


class UserFeedView(rest_framework.generics.ListAPIView):
    serializer_class = user.serializers.PromoFeedSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated]
    pagination_class = core.pagination.CustomLimitOffsetPagination

    def get_queryset(self):
        user = self.request.user

        user_age = user.other.get('age')
        user_country = user.other.get('country').lower()
        active_filter = self.request.query_params.get('active')

        return business.models.Promo.objects.get_feed_for_user(
            user,
            active_filter=active_filter,
            user_country=user_country,
            user_age=user_age,
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        category_param = self.request.query_params.get('category')

        if category_param:
            needle = f'"{category_param.lower()}"'
            queryset = queryset.filter(target__categories__icontains=needle)

        return queryset

    def list(self, request, *args, **kwargs):
        query_serializer = user.serializers.UserFeedQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)
        self.validated_query_params = query_serializer.validated_data

        return super().list(request, *args, **kwargs)


class UserPromoLikeView(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get_promo_object(self, promo_id):
        return django.shortcuts.get_object_or_404(
            business.models.Promo,
            id=promo_id,
        )

    def post(self, request, id):
        """Add a like to the promo code."""
        with django.db.transaction.atomic():
            promo = self.get_promo_object(id)

            like_obj, created = user.models.PromoLike.objects.get_or_create(
                user=request.user,
                promo=promo,
            )

            if created:
                promo.like_count = django.db.models.F('like_count') + 1
                promo.save(update_fields=['like_count'])
                promo.refresh_from_db()

            return rest_framework.response.Response(
                {'status': 'ok'},
                status=rest_framework.status.HTTP_200_OK,
            )

    def delete(self, request, id):
        """Remove a like from the promo code."""
        with django.db.transaction.atomic():
            promo = self.get_promo_object(id)

            # Idempotency: if the like doesn't exist,
            # do nothing and still return 200 OK.
            like_instance = user.models.PromoLike.objects.filter(
                user=request.user,
                promo=promo,
            ).first()

            if like_instance:
                like_instance.delete()
                promo.like_count = django.db.models.F('like_count') - 1
                promo.save(update_fields=['like_count'])
                promo.refresh_from_db()

            return rest_framework.response.Response(
                {'status': 'ok'},
                status=rest_framework.status.HTTP_200_OK,
            )


class PromoObjectMixin:
    """Mixin for retrieving the Promo object and saving it to self.promo"""

    def dispatch(self, request, *args, **kwargs):
        self.promo = django.shortcuts.get_object_or_404(
            business.models.Promo.objects.select_for_update(),
            pk=self.kwargs.get('promo_id'),
        )
        return super().dispatch(request, *args, **kwargs)


class PromoCommentListCreateView(
    PromoObjectMixin,
    rest_framework.generics.ListCreateAPIView,
):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    pagination_class = core.pagination.CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return user.serializers.CommentCreateSerializer
        return user.serializers.CommentSerializer

    def get_queryset(self):
        return user.models.PromoComment.objects.filter(
            promo=self.promo,
        ).select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, promo=self.promo)
        self.promo.comment_count = django.db.models.F('comment_count') + 1
        self.promo.save(update_fields=['comment_count'])

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        response_serializer = user.serializers.CommentSerializer(
            create_serializer.instance,
        )
        headers = self.get_success_headers(response_serializer.data)
        return rest_framework.response.Response(
            response_serializer.data,
            status=rest_framework.status.HTTP_201_CREATED,
            headers=headers,
        )

    def list(self, request, *args, **kwargs):
        query_serializer = user.serializers.UserFeedQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)

        return super().list(request, *args, **kwargs)


class PromoCommentDetailView(
    PromoObjectMixin,
    rest_framework.generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        user.permissions.IsOwnerOrReadOnly,
    ]
    lookup_url_kwarg = 'comment_id'

    http_method_names = ['get', 'put', 'delete', 'options', 'head']

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return user.serializers.CommentUpdateSerializer
        return user.serializers.CommentSerializer

    def get_queryset(self):
        return user.models.PromoComment.objects.filter(
            promo=self.promo,
        ).select_related('author')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        update_serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        update_serializer.is_valid(raise_exception=True)
        self.perform_update(update_serializer)

        response_serializer = user.serializers.CommentSerializer(instance)
        return rest_framework.response.Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        promo = instance.promo
        promo.comment_count = django.db.models.F('comment_count') - 1
        promo.save(update_fields=['comment_count'])

        return rest_framework.response.Response(
            {'status': 'ok'},
            status=rest_framework.status.HTTP_200_OK,
        )


class PromoActivateView(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]
    allowed_methods = ['post', 'options', 'head']

    def _validate_targeting(self, user_, promo):
        user_age = user_.other.get('age')
        user_country = user_.other.get('country').lower()
        target = promo.target

        if not target:
            return None

        if target.get('country') and user_country != target['country'].lower():
            return rest_framework.response.Response(
                {'error': 'Targeting mismatch: country.'},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )
        if target.get('age_from') and (
            user_age is None or user_age < target['age_from']
        ):
            return rest_framework.response.Response(
                {'error': 'Targeting mismatch: age.'},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )
        if target.get('age_until') and (
            user_age is None or user_age > target['age_until']
        ):
            return rest_framework.response.Response(
                {'error': 'Targeting mismatch: age.'},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )
        return None

    def _validate_is_active(self, promo):
        if not promo.active or not promo.is_active:
            return rest_framework.response.Response(
                {'error': 'Promo is not active.'},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )
        return None

    def _validate_antifraud(self, user_, promo):
        antifraud_response = (
            user.antifraud_service.antifraud_service.get_verdict(
                user_.email,
                str(promo.id),
            )
        )
        if not antifraud_response.get('ok'):
            return rest_framework.response.Response(
                {'error': 'Activation forbidden by anti-fraud system.'},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )
        return None

    def _activate_code(self, user_, promo):
        try:
            with django.db.transaction.atomic():
                promo_for_update = (
                    business.models.Promo.objects.select_for_update().get(
                        id=promo.id,
                    )
                )
                promo_code_value = None

                if (
                    promo_for_update.mode
                    == business.constants.PROMO_MODE_COMMON
                ):
                    if (
                        promo_for_update.used_count
                        < promo_for_update.max_count
                    ):
                        promo_for_update.used_count += 1
                        promo_for_update.save(update_fields=['used_count'])
                        promo_code_value = promo_for_update.promo_common
                    else:
                        raise ValueError('No common codes left.')

                elif (
                    promo_for_update.mode
                    == business.constants.PROMO_MODE_UNIQUE
                ):
                    unique_code = promo_for_update.unique_codes.filter(
                        is_used=False,
                    ).first()
                    if unique_code:
                        unique_code.is_used = True
                        unique_code.used_at = django.utils.timezone.now()
                        unique_code.save(update_fields=['is_used', 'used_at'])
                        promo_code_value = unique_code.code
                    else:
                        raise ValueError('No unique codes left.')

                if promo_code_value:
                    user.models.PromoActivationHistory.objects.create(
                        user=user_,
                        promo=promo,
                    )
                    serializer = user.serializers.PromoActivationSerializer(
                        data={'promo': promo_code_value},
                    )
                    serializer.is_valid(raise_exception=True)
                    return rest_framework.response.Response(
                        serializer.data,
                        status=rest_framework.status.HTTP_200_OK,
                    )

                raise ValueError('Promo code could not be activated.')

        except ValueError as e:
            return rest_framework.response.Response(
                {'error': str(e)},
                status=rest_framework.status.HTTP_403_FORBIDDEN,
            )

    def post(self, request, id):
        promo = django.shortcuts.get_object_or_404(
            business.models.Promo,
            id=id,
        )
        user_ = request.user

        if (response := self._validate_targeting(user_, promo)) is not None:
            return response

        if (response := self._validate_is_active(promo)) is not None:
            return response

        if (response := self._validate_antifraud(user_, promo)) is not None:
            return response

        return self._activate_code(user_, promo)


class PromoHistoryView(rest_framework.generics.ListAPIView):
    """
    Returns the history of activated promo codes for the current user.
    """

    serializer_class = user.serializers.UserPromoDetailSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated]
    pagination_class = core.pagination.CustomLimitOffsetPagination

    def get_queryset(self):
        user = self.request.user

        queryset = business.models.Promo.objects.filter(
            activations_history__user=user,
        ).order_by('-activations_history__activated_at')

        return queryset  # noqa: RET504
