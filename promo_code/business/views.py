import re

import django.db.models
import pycountry
import rest_framework.exceptions
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


class PromoCreateView(rest_framework.views.APIView):
    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
    ]
    serializer_class = business.serializers.PromoCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            instance = serializer.save()
            return rest_framework.response.Response(
                {'id': str(instance.id)},
                status=rest_framework.status.HTTP_201_CREATED,
            )

        return rest_framework.response.Response(
            serializer.errors,
            status=rest_framework.status.HTTP_400_BAD_REQUEST,
        )


class CompanyPromoListView(rest_framework.generics.ListAPIView):
    permission_classes = [
        rest_framework.permissions.IsAuthenticated,
        business.permissions.IsCompanyUser,
    ]
    serializer_class = business.serializers.PromoReadOnlySerializer
    pagination_class = business.pagination.CustomLimitOffsetPagination

    def get_queryset(self):
        queryset = business.models.Promo.objects.filter(
            company=self.request.user,
        )

        countries = [
            country.strip()
            for group in self.request.query_params.getlist('country', [])
            for country in group.split(',')
            if country.strip()
        ]

        if countries:
            regex_pattern = r'(' + '|'.join(map(re.escape, countries)) + ')'
            queryset = queryset.filter(
                django.db.models.Q(target__country__iregex=regex_pattern)
                | django.db.models.Q(target__country__isnull=True),
            )

        sort_by = self.request.query_params.get('sort_by')
        if sort_by in ['active_from', 'active_until']:
            queryset = queryset.order_by(f'-{sort_by}')
        else:
            queryset = queryset.order_by('-created_at')  # noqa: R504

        return queryset  # noqa: R504

    def list(self, request, *args, **kwargs):
        try:
            self.validate_query_params()
        except rest_framework.exceptions.ValidationError as e:
            return rest_framework.response.Response(
                e.detail,
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        return super().list(request, *args, **kwargs)

    def validate_query_params(self):
        self._validate_allowed_params()
        errors = {}
        self._validate_countries(errors)
        self._validate_sort_by(errors)
        self._validate_offset()
        self._validate_limit()
        if errors:
            raise rest_framework.exceptions.ValidationError(errors)

    def _validate_allowed_params(self):
        allowed_params = {'country', 'limit', 'offset', 'sort_by'}
        unexpected_params = (
            set(self.request.query_params.keys()) - allowed_params
        )

        if unexpected_params:
            raise rest_framework.exceptions.ValidationError('Invalid params.')

    def _validate_countries(self, errors):
        countries = self.request.query_params.getlist('country', [])
        country_list = []

        for country_group in countries:
            parts = [part.strip() for part in country_group.split(',')]

            if any(part == '' for part in parts):
                raise rest_framework.exceptions.ValidationError(
                    'Invalid country format.',
                )

            country_list.extend(parts)

        country_list = [c.strip().upper() for c in country_list if c.strip()]

        invalid_countries = []

        for code in country_list:
            if len(code) != 2:
                invalid_countries.append(code)
                continue

            try:
                pycountry.countries.lookup(code)
            except LookupError:
                invalid_countries.append(code)

        if invalid_countries:
            errors['country'] = (
                f'Invalid country codes: {", ".join(invalid_countries)}'
            )

    def _validate_sort_by(self, errors):
        sort_by = self.request.query_params.get('sort_by')
        if sort_by and sort_by not in ['active_from', 'active_until']:
            errors['sort_by'] = (
                'Invalid sort_by parameter. '
                'Available values: active_from, active_until'
            )

    def _validate_offset(self):
        offset = self.request.query_params.get('offset')
        if offset is not None:
            try:
                offset = int(offset)
            except (TypeError, ValueError):
                raise rest_framework.exceptions.ValidationError(
                    'Invalid offset format.',
                )

            if offset < 0:
                raise rest_framework.exceptions.ValidationError(
                    'Offset cannot be negative.',
                )

    def _validate_limit(self):
        limit = self.request.query_params.get('limit')

        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                raise rest_framework.exceptions.ValidationError(
                    'Invalid limit format.',
                )

            if limit < 0:
                raise rest_framework.exceptions.ValidationError(
                    'Limit cannot be negative.',
                )
