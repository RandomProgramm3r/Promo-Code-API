import re

import django.db.models
import rest_framework.generics
import rest_framework.permissions
import rest_framework.response
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import business.models
import business.pagination
import business.permissions
import business.serializers
import core.views


class CompanySignUpView(
    core.views.BaseCustomResponseMixin,
    rest_framework.generics.CreateAPIView,
):
    serializer_class = business.serializers.CompanySignUpSerializer

    def post(self, request):
        try:
            serializer = business.serializers.CompanySignUpSerializer(
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
        except (
            rest_framework.serializers.ValidationError,
            rest_framework_simplejwt.exceptions.TokenError,
        ) as e:
            if isinstance(e, rest_framework.serializers.ValidationError):
                return self.handle_validation_error()

            raise rest_framework_simplejwt.exceptions.InvalidToken(str(e))

        company = serializer.save()

        refresh = rest_framework_simplejwt.tokens.RefreshToken()
        refresh['user_type'] = 'company'
        refresh['company_id'] = str(company.id)
        refresh['token_version'] = company.token_version

        access_token = refresh.access_token
        access_token['user_type'] = 'company'
        access_token['company_id'] = str(company.id)
        refresh['token_version'] = company.token_version

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )


class CompanySignInView(
    core.views.BaseCustomResponseMixin,
    rest_framework_simplejwt.views.TokenObtainPairView,
):
    serializer_class = business.serializers.CompanySignInSerializer

    def post(self, request):
        try:
            serializer = business.serializers.CompanySignInSerializer(
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
        except (
            rest_framework.serializers.ValidationError,
            rest_framework_simplejwt.exceptions.TokenError,
        ) as e:
            if isinstance(e, rest_framework.serializers.ValidationError):
                return self.handle_validation_error()

            raise rest_framework_simplejwt.exceptions.InvalidToken(str(e))

        company = business.models.Company.objects.get(
            email=serializer.validated_data['email'],
        )
        company.token_version += 1
        company.save()

        refresh = rest_framework_simplejwt.tokens.RefreshToken()
        refresh['user_type'] = 'company'
        refresh['company_id'] = str(company.id)
        refresh['token_version'] = company.token_version

        access_token = refresh.access_token
        access_token['user_type'] = 'company'
        access_token['company_id'] = str(company.id)

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )


class CompanyTokenRefreshView(rest_framework_simplejwt.views.TokenRefreshView):
    serializer_class = business.serializers.CompanyTokenRefreshSerializer


class PromoCreateView(rest_framework.generics.CreateAPIView):
    """
    View for creating a new promo (POST).
    """

    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
    ]
    serializer_class = business.serializers.PromoCreateSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        response_data = {'id': str(instance.id)}

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_201_CREATED,
            headers=headers,
        )


class CompanyPromoListView(rest_framework.generics.ListAPIView):
    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
    ]
    serializer_class = business.serializers.PromoReadOnlySerializer
    pagination_class = business.pagination.CustomLimitOffsetPagination

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        serializer = business.serializers.PromoListQuerySerializer(
            data=request.query_params,
        )
        serializer.is_valid(raise_exception=True)
        request.validated_query_params = serializer.validated_data

    def get_queryset(self):
        params = self.request.validated_query_params
        countries = [c.upper() for c in params.get('countries', [])]
        sort_by = params.get('sort_by')

        queryset = business.models.Promo.objects.for_company(self.request.user)

        if countries:
            regex_pattern = r'(' + '|'.join(map(re.escape, countries)) + ')'
            queryset = queryset.filter(
                django.db.models.Q(target__country__iregex=regex_pattern)
                | django.db.models.Q(target__country__isnull=True),
            )

        ordering = f'-{sort_by}' if sort_by else '-created_at'

        return queryset.order_by(ordering)


class CompanyPromoDetailView(rest_framework.generics.RetrieveUpdateAPIView):
    """
    Retrieve (GET) and partially update (PATCH) detailed information
    about a company’s promo.
    """

    http_method_names = ['get', 'patch', 'options', 'head']

    serializer_class = business.serializers.PromoDetailSerializer

    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
        business.permissions.IsPromoOwner,
    ]

    lookup_field = 'id'

    # Use an enriched base queryset without pre-filtering by company,
    # so that ownership mismatches raise 403 Forbidden (not 404 Not Found).
    queryset = business.models.Promo.objects.with_related()
