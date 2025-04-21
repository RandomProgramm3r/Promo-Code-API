import uuid

import django.contrib.auth.password_validation
import django.core.exceptions
import django.core.validators
import pycountry
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.tokens

import business.constants
import business.models as business_models
import business.validators


class CompanySignUpSerializer(rest_framework.serializers.ModelSerializer):
    id = rest_framework.serializers.UUIDField(read_only=True)
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        min_length=business.constants.COMPANY_PASSWORD_MIN_LENGTH,
        max_length=business.constants.COMPANY_PASSWORD_MAX_LENGTH,
        style={'input_type': 'password'},
    )
    name = rest_framework.serializers.CharField(
        required=True,
        min_length=business.constants.COMPANY_NAME_MIN_LENGTH,
        max_length=business.constants.COMPANY_NAME_MAX_LENGTH,
    )
    email = rest_framework.serializers.EmailField(
        required=True,
        min_length=business.constants.COMPANY_EMAIL_MIN_LENGTH,
        max_length=business.constants.COMPANY_EMAIL_MAX_LENGTH,
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
        min_value=business.constants.TARGET_AGE_MIN,
        max_value=business.constants.TARGET_AGE_MAX,
        required=False,
    )
    age_until = rest_framework.serializers.IntegerField(
        min_value=business.constants.TARGET_AGE_MIN,
        max_value=business.constants.TARGET_AGE_MAX,
        required=False,
    )
    country = rest_framework.serializers.CharField(
        max_length=business.constants.TARGET_COUNTRY_CODE_LENGTH,
        min_length=business.constants.TARGET_COUNTRY_CODE_LENGTH,
        required=False,
    )
    categories = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.TARGET_CATEGORY_MIN_LENGTH,
            max_length=business.constants.TARGET_CATEGORY_MAX_LENGTH,
        ),
        max_length=business.constants.TARGET_CATEGORY_MAX_ITEMS,
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
            try:
                pycountry.countries.lookup(country.strip().upper())
                data['country'] = country
            except LookupError:
                raise rest_framework.serializers.ValidationError(
                    {'country': 'Invalid ISO 3166-1 alpha-2 country code.'},
                )

        return data


class PromoCreateSerializer(rest_framework.serializers.ModelSerializer):
    description = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_DESC_MIN_LENGTH,
        max_length=business.constants.PROMO_DESC_MAX_LENGTH,
        required=True,
    )
    image_url = rest_framework.serializers.CharField(
        required=False,
        max_length=business.constants.PROMO_IMAGE_URL_MAX_LENGTH,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    target = TargetSerializer(required=True, allow_null=True)
    promo_common = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_COMMON_CODE_MIN_LENGTH,
        max_length=business.constants.PROMO_COMMON_CODE_MAX_LENGTH,
        required=False,
        allow_null=True,
    )
    promo_unique = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.PROMO_UNIQUE_CODE_MIN_LENGTH,
            max_length=business.constants.PROMO_UNIQUE_CODE_MAX_LENGTH,
        ),
        min_length=business.constants.PROMO_UNIQUE_LIST_MIN_ITEMS,
        max_length=business.constants.PROMO_UNIQUE_LIST_MAX_ITEMS,
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
        data = super().validate(data)
        validator = business.validators.PromoValidator(data=data)
        return validator.validate()

    def create(self, validated_data):
        target_data = validated_data.pop('target')
        promo_common = validated_data.pop('promo_common', None)
        promo_unique = validated_data.pop('promo_unique', None)

        return business_models.Promo.objects.create_promo(
            user=self.context['request'].user,
            target_data=target_data,
            promo_common=promo_common,
            promo_unique=promo_unique,
            **validated_data,
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['target'] = instance.target

        if instance.mode == business.constants.PROMO_MODE_UNIQUE:
            data['promo_unique'] = [
                code.code for code in instance.unique_codes.all()
            ]
            data.pop('promo_common', None)
        else:
            data.pop('promo_unique', None)

        return data


class PromoReadOnlySerializer(rest_framework.serializers.ModelSerializer):
    promo_id = rest_framework.serializers.UUIDField(
        source='id',
        read_only=True,
    )
    company_id = rest_framework.serializers.UUIDField(
        source='company.id',
        read_only=True,
    )
    company_name = rest_framework.serializers.CharField(
        source='company.name',
        read_only=True,
    )
    target = TargetSerializer()

    promo_unique = rest_framework.serializers.SerializerMethodField()
    like_count = rest_framework.serializers.SerializerMethodField()
    used_count = rest_framework.serializers.IntegerField(
        source='get_used_codes_count',
        read_only=True,
    )
    active = rest_framework.serializers.BooleanField(
        source='is_active',
        read_only=True,
    )

    class Meta:
        model = business_models.Promo
        fields = (
            'promo_id',
            'company_id',
            'company_name',
            'description',
            'image_url',
            'target',
            'max_count',
            'active_from',
            'active_until',
            'mode',
            'promo_common',
            'promo_unique',
            'like_count',
            'used_count',
            'active',
        )

    def get_promo_unique(self, obj):
        return obj.get_available_unique_codes

    def get_like_count(self, obj):
        # TODO
        return 0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.mode == business.constants.PROMO_MODE_COMMON:
            data.pop('promo_unique', None)
        else:
            data.pop('promo_common', None)

        return data


class PromoDetailSerializer(rest_framework.serializers.ModelSerializer):
    promo_id = rest_framework.serializers.UUIDField(
        source='id',
        read_only=True,
    )
    description = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_DESC_MIN_LENGTH,
        max_length=business.constants.PROMO_DESC_MAX_LENGTH,
        required=True,
    )
    image_url = rest_framework.serializers.CharField(
        required=False,
        max_length=business.constants.PROMO_IMAGE_URL_MAX_LENGTH,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    target = TargetSerializer(allow_null=True, required=False)
    promo_unique = rest_framework.serializers.SerializerMethodField()
    company_name = rest_framework.serializers.CharField(
        source='company.name',
        read_only=True,
    )
    like_count = rest_framework.serializers.SerializerMethodField()
    used_count = rest_framework.serializers.IntegerField(
        source='get_used_codes_count',
        read_only=True,
    )

    class Meta:
        model = business_models.Promo
        fields = (
            'promo_id',
            'description',
            'image_url',
            'target',
            'max_count',
            'active_from',
            'active_until',
            'mode',
            'promo_common',
            'promo_unique',
            'company_name',
            'like_count',
            'used_count',
        )

    def get_promo_unique(self, obj):
        return obj.get_available_unique_codes

    def update(self, instance, validated_data):
        target_data = validated_data.pop('target', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if target_data is not None:
            instance.target = target_data

        instance.save()
        return instance

    def validate(self, data):
        data = super().validate(data)
        validator = business.validators.PromoValidator(
            data=data,
            instance=self.instance,
        )
        return validator.validate()

    def get_like_count(self, obj):
        # TODO
        return 0
