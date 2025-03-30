import uuid

import django.contrib.auth.password_validation
import django.core.exceptions
import django.core.validators
import pycountry
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import business.models as business_models
import business.validators


class CompanySignUpSerializer(rest_framework.serializers.ModelSerializer):
    id = rest_framework.serializers.UUIDField(read_only=True)
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        min_length=8,
        max_length=60,
        style={'input_type': 'password'},
    )
    name = rest_framework.serializers.CharField(
        required=True,
        min_length=5,
        max_length=50,
    )
    email = rest_framework.serializers.EmailField(
        required=True,
        min_length=8,
        max_length=120,
        validators=[
            business.validators.UniqueEmailValidator(
                'This email address is already registered.',
                'email_conflict',
            ),
        ],
    )

    class Meta:
        model = business_models.Company
        fields = (
            'id',
            'name',
            'email',
            'password',
        )

    def create(self, validated_data):
        try:
            company = business_models.Company.objects.create_company(
                email=validated_data['email'],
                name=validated_data['name'],
                password=validated_data['password'],
            )
            company.token_version += 1
            company.save()
            return company
        except django.core.exceptions.ValidationError as e:
            raise rest_framework.serializers.ValidationError(e.messages)


class CompanySignInSerializer(
    rest_framework.serializers.Serializer,
):
    email = rest_framework.serializers.EmailField(required=True)
    password = rest_framework.serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise rest_framework.exceptions.ValidationError(
                {'detail': 'Both email and password are required'},
                code='required',
            )

        try:
            company = business_models.Company.objects.get(email=email)
        except business_models.Company.DoesNotExist:
            raise rest_framework.serializers.ValidationError(
                'Invalid credentials',
            )

        if not company.is_active or not company.check_password(password):
            raise rest_framework.exceptions.AuthenticationFailed(
                {'detail': 'Invalid credentials or inactive account'},
                code='authentication_failed',
            )

        return attrs


class CompanyTokenRefreshSerializer(
    rest_framework_simplejwt.serializers.TokenRefreshSerializer,
):
    def validate(self, attrs):
        refresh = rest_framework_simplejwt.tokens.RefreshToken(
            attrs['refresh'],
        )
        user_type = refresh.payload.get('user_type', 'user')

        if user_type != 'company':
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'This refresh endpoint is for company tokens only',
            )

        company_id = refresh.payload.get('company_id')
        if not company_id:
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Company ID missing in token',
            )

        try:
            company = business_models.Company.objects.get(
                id=uuid.UUID(company_id),
            )
        except business_models.Company.DoesNotExist:
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Company not found',
            )

        token_version = refresh.payload.get('token_version', 0)
        if company.token_version != token_version:
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Token is blacklisted',
            )

        new_refresh = rest_framework_simplejwt.tokens.RefreshToken()
        new_refresh['user_type'] = 'company'
        new_refresh['company_id'] = str(company.id)
        new_refresh['token_version'] = company.token_version

        return {
            'access': str(new_refresh.access_token),
            'refresh': str(new_refresh),
        }


class TargetSerializer(rest_framework.serializers.Serializer):
    age_from = rest_framework.serializers.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        allow_null=True,
    )
    age_until = rest_framework.serializers.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        allow_null=True,
    )
    country = rest_framework.serializers.CharField(
        max_length=2,
        min_length=2,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    categories = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=2,
            max_length=20,
        ),
        max_length=20,
        required=False,
        allow_empty=True,
    )

    def validate(self, data):
        age_from = data.get('age_from')
        age_until = data.get('age_until')
        if (
            age_from is not None
            and age_until is not None
            and age_from > age_until
        ):
            raise rest_framework.serializers.ValidationError(
                {'age_until': 'Must be greater than or equal to age_from.'},
            )

        country = data.get('country')
        if country:
            country = country.strip().upper()
            try:
                pycountry.countries.lookup(country)
                data['country'] = country
            except LookupError:
                raise rest_framework.serializers.ValidationError(
                    {'country': 'Invalid ISO 3166-1 alpha-2 country code.'},
                )

        return data


class PromoCreateSerializer(rest_framework.serializers.ModelSerializer):
    description = rest_framework.serializers.CharField(
        min_length=10,
        max_length=300,
        required=True,
    )
    image_url = rest_framework.serializers.CharField(
        required=False,
        max_length=350,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    target = TargetSerializer(required=True)
    promo_common = rest_framework.serializers.CharField(
        min_length=5,
        max_length=30,
        required=False,
        allow_null=True,
    )
    promo_unique = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=3,
            max_length=30,
        ),
        min_length=1,
        max_length=5000,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = business_models.Promo
        fields = (
            'description',
            'image_url',
            'target',
            'max_count',
            'active_from',
            'active_until',
            'mode',
            'promo_common',
            'promo_unique',
        )

    def validate(self, data):
        mode = data.get('mode')
        promo_common = data.get('promo_common')
        promo_unique = data.get('promo_unique')
        max_count = data.get('max_count')

        if mode == business_models.Promo.MODE_COMMON:
            if not promo_common:
                raise rest_framework.serializers.ValidationError(
                    {
                        'promo_common': (
                            'This field is required for COMMON mode.'
                        ),
                    },
                )

            if promo_unique is not None:
                raise rest_framework.serializers.ValidationError(
                    {
                        'promo_unique': (
                            'This field is not allowed for COMMON mode.'
                        ),
                    },
                )

            if max_count < 0 or max_count > 100000000:
                raise rest_framework.serializers.ValidationError(
                    {
                        'max_count': (
                            'Must be between 0 and 100,000,000 '
                            'for COMMON mode.'
                        ),
                    },
                )

        elif mode == business_models.Promo.MODE_UNIQUE:
            if not promo_unique:
                raise rest_framework.serializers.ValidationError(
                    {
                        'promo_unique': (
                            'This field is required for UNIQUE mode.'
                        ),
                    },
                )

            if promo_common is not None:
                raise rest_framework.serializers.ValidationError(
                    {
                        'promo_common': (
                            'This field is not allowed for UNIQUE mode.'
                        ),
                    },
                )

            if max_count != 1:
                raise rest_framework.serializers.ValidationError(
                    {'max_count': 'Must be 1 for UNIQUE mode.'},
                )

        else:
            raise rest_framework.serializers.ValidationError(
                {'mode': 'Invalid mode.'},
            )

        active_from = data.get('active_from')
        active_until = data.get('active_until')
        if active_from and active_until and active_from > active_until:
            raise rest_framework.serializers.ValidationError(
                {'active_until': 'Must be after or equal to active_from.'},
            )

        return data

    def create(self, validated_data):
        target_data = validated_data.pop('target')
        promo_common = validated_data.pop('promo_common', None)
        promo_unique = validated_data.pop('promo_unique', None)
        mode = validated_data['mode']

        user = self.context['request'].user
        validated_data['company'] = user

        promo = business_models.Promo.objects.create(
            **validated_data,
            target=target_data,
        )

        if mode == business_models.Promo.MODE_COMMON:
            promo.promo_common = promo_common
            promo.save()
        elif mode == business_models.Promo.MODE_UNIQUE and promo_unique:
            promo_codes = [
                business_models.PromoCode(promo=promo, code=code)
                for code in promo_unique
            ]
            business_models.PromoCode.objects.bulk_create(promo_codes)

        return promo

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['target'] = instance.target

        if instance.mode == business_models.Promo.MODE_UNIQUE:
            data['promo_unique'] = [
                code.code for code in instance.unique_codes.all()
            ]
            data.pop('promo_common', None)
        else:
            data.pop('promo_unique', None)

        return data
