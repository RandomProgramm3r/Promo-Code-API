import re

import django.db.models
import rest_framework.generics
import rest_framework.permissions
import rest_framework.response
import rest_framework.status
import rest_framework_simplejwt.views

import business.models
import business.pagination
import business.permissions
import business.serializers
import business.utils.auth
import business.utils.tokens


class CompanySignUpView(rest_framework.generics.CreateAPIView):
    """
    Company registration endpoint that returns JWT tokens.
    """

    serializer_class = business.serializers.CompanySignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()

        return rest_framework.response.Response(
            business.utils.tokens.generate_company_tokens(company),
            status=rest_framework.status.HTTP_200_OK,
        )


class CompanySignInView(rest_framework.generics.GenericAPIView):
    """
    Company authentication endpoint that issues new JWT tokens
    and bumps token_version.
    """

    serializer_class = business.serializers.CompanySignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        company = serializer.validated_data['company']
        company = business.utils.auth.bump_company_token_version(company)

        return rest_framework.response.Response(
            business.utils.tokens.generate_company_tokens(company),
            status=rest_framework.status.HTTP_200_OK,
        )


class CompanyTokenRefreshView(rest_framework_simplejwt.views.TokenRefreshView):
    """
    Refresh endpoint for company tokens only.
    """

    serializer_class = business.serializers.CompanyTokenRefreshSerializer


class CompanyPromoListCreateView(rest_framework.generics.ListCreateAPIView):
    """
    View for listing (GET) and creating (POST) company promos.
    """

    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
    ]
    # Pagination is only needed for GET (listing)
    pagination_class = business.pagination.CustomLimitOffsetPagination

    _validated_query_params = {}

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return business.serializers.PromoCreateSerializer

        return business.serializers.PromoReadOnlySerializer

    def list(self, request, *args, **kwargs):
        query_serializer = business.serializers.PromoListQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)
        self._validated_query_params = query_serializer.validated_data

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        params = self._validated_query_params
        countries = [c.upper() for c in params.get('countries', [])]
        sort_by = params.get('sort_by')

        queryset = business.models.Promo.objects.for_company(self.request.user)

        if countries:
            # Using a regular expression for case-insensitive searching
            regex_pattern = r'(' + '|'.join(map(re.escape, countries)) + ')'
            country_filter = django.db.models.Q(
                target__country__iregex=regex_pattern,
            )

            # Include promos where the country is not specified
            queryset = queryset.filter(
                country_filter
                | django.db.models.Q(target__country__isnull=True),
            )

        ordering = f'-{sort_by}' if sort_by else '-created_at'

        return queryset.order_by(ordering)

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
