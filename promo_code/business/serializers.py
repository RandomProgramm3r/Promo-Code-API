import uuid

import django.contrib.auth.password_validation
import django.db.transaction
import pycountry
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.tokens

import business.constants
import business.models
import business.utils.tokens
import core.serializers
import core.utils.auth


class CompanySignUpSerializer(rest_framework.serializers.ModelSerializer):
    id = rest_framework.serializers.UUIDField(read_only=True)
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        style={'input_type': 'password'},
        min_length=business.constants.COMPANY_PASSWORD_MIN_LENGTH,
        max_length=business.constants.COMPANY_PASSWORD_MAX_LENGTH,
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
    )

    class Meta:
        model = business.models.Company
        fields = ('id', 'name', 'email', 'password')

    @django.db.transaction.atomic
    def create(self, validated_data):
        try:
            company = business.models.Company.objects.create_company(
                **validated_data,
            )
        except django.db.IntegrityError:
            exc = rest_framework.exceptions.APIException(
                detail={
                    'email': 'This email address is already registered.',
                },
            )
            exc.status_code = 409
            raise exc

        return core.utils.auth.bump_token_version(company)


class CompanySignInSerializer(rest_framework.serializers.Serializer):
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
            raise rest_framework.serializers.ValidationError(
                'Both email and password are required.',
            )

        try:
            company = business.models.Company.objects.get(email=email)
        except business.models.Company.DoesNotExist:
            raise rest_framework.serializers.ValidationError(
                'Invalid credentials.',
            )

        if not company.is_active or not company.check_password(password):
            raise rest_framework.exceptions.AuthenticationFailed(
                {'detail': 'Invalid credentials or inactive account'},
                code='authentication_failed',
            )

        attrs['company'] = company
        return attrs


class CompanyTokenRefreshSerializer(
    rest_framework_simplejwt.serializers.TokenRefreshSerializer,
):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        refresh = rest_framework_simplejwt.tokens.RefreshToken(
            attrs['refresh'],
        )
        company = self.get_active_company_from_token(refresh)

        company = core.utils.auth.bump_token_version(company)

        return business.utils.tokens.generate_company_tokens(company)

    def get_active_company_from_token(self, token):
        if token.payload.get('user_type') != 'company':
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'This refresh endpoint is for company tokens only',
            )

        company_id = token.payload.get('company_id')
        try:
            company_uuid = uuid.UUID(company_id)
        except (TypeError, ValueError):
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Invalid or missing company_id in token',
            )

        try:
            company = business.models.Company.objects.get(
                id=company_uuid,
                is_active=True,
            )
        except business.models.Company.DoesNotExist:
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Company not found or inactive',
            )

        token_version = token.payload.get('token_version', 0)
        if company.token_version != token_version:
            raise rest_framework_simplejwt.exceptions.InvalidToken(
                'Token is blacklisted',
            )

        return company


class CountryField(rest_framework.serializers.CharField):
    """
    Custom field for validating country codes according to ISO 3166-1 alpha-2.
    """

    def __init__(self, **kwargs):
        kwargs['allow_blank'] = False
        kwargs['min_length'] = business.constants.TARGET_COUNTRY_CODE_LENGTH
        kwargs['max_length'] = business.constants.TARGET_COUNTRY_CODE_LENGTH
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        code = super().to_internal_value(data)
        try:
            pycountry.countries.lookup(code.upper())
        except LookupError:
            raise rest_framework.serializers.ValidationError(
                'Invalid ISO 3166-1 alpha-2 country code.',
            )
        return code


class MultiCountryField(rest_framework.serializers.ListField):
    """
    Custom field for handling multiple country codes,
    passed either as a comma-separated list or as multiple parameters.
    """

    def __init__(self, **kwargs):
        kwargs['child'] = CountryField()
        kwargs['allow_empty'] = False
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if not data or not isinstance(data, list):
            raise rest_framework.serializers.ValidationError(
                'At least one country must be specified.',
            )

        # (&country=us,fr)
        if len(data) == 1 and ',' in data[0]:
            countries_str = data[0]
            if '' in [s.strip() for s in countries_str.split(',')]:
                raise rest_framework.serializers.ValidationError(
                    'Invalid country format.',
                )
            data = [country.strip() for country in countries_str.split(',')]

        if any(not item for item in data):
            raise rest_framework.serializers.ValidationError(
                'Empty value for country is not allowed.',
            )

        return super().to_internal_value(data)


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
    country = CountryField(required=False)

    categories = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.TARGET_CATEGORY_MIN_LENGTH,
            max_length=business.constants.TARGET_CATEGORY_MAX_LENGTH,
            allow_blank=False,
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
        return data


class BasePromoSerializer(rest_framework.serializers.ModelSerializer):
    """
    Base serializer for promo, containing validation and representation logic.
    """

    image_url = rest_framework.serializers.URLField(
        required=False,
        allow_blank=False,
        max_length=business.constants.PROMO_IMAGE_URL_MAX_LENGTH,
    )
    description = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_DESC_MIN_LENGTH,
        max_length=business.constants.PROMO_DESC_MAX_LENGTH,
        required=True,
    )
    target = TargetSerializer(required=True, allow_null=True)
    promo_common = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_COMMON_CODE_MIN_LENGTH,
        max_length=business.constants.PROMO_COMMON_CODE_MAX_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=False,
    )
    promo_unique = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.PROMO_UNIQUE_CODE_MIN_LENGTH,
            max_length=business.constants.PROMO_UNIQUE_CODE_MAX_LENGTH,
            allow_blank=False,
        ),
        min_length=business.constants.PROMO_UNIQUE_LIST_MIN_ITEMS,
        max_length=business.constants.PROMO_UNIQUE_LIST_MAX_ITEMS,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = business.models.Promo
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
        """
        Main validation method.
        Determines the mode and calls the corresponding validation method.
        """

        mode = data.get('mode', getattr(self.instance, 'mode', None))

        if mode == business.constants.PROMO_MODE_COMMON:
            self._validate_common(data)
        elif mode == business.constants.PROMO_MODE_UNIQUE:
            self._validate_unique(data)
        elif mode is None:
            raise rest_framework.serializers.ValidationError(
                {'mode': 'This field is required.'},
            )
        else:
            raise rest_framework.serializers.ValidationError(
                {'mode': 'Invalid mode.'},
            )

        return data

    def _validate_common(self, data):
        """
        Validations for COMMON promo mode.
        """

        if 'promo_unique' in data and data['promo_unique'] is not None:
            raise rest_framework.serializers.ValidationError(
                {'promo_unique': 'This field is not allowed for COMMON mode.'},
            )

        if self.instance is None and not data.get('promo_common'):
            raise rest_framework.serializers.ValidationError(
                {'promo_common': 'This field is required for COMMON mode.'},
            )

        new_max_count = data.get('max_count')
        if self.instance and new_max_count is not None:
            used_count = self.instance.get_used_codes_count
            if used_count > new_max_count:
                raise rest_framework.serializers.ValidationError(
                    {
                        'max_count': (
                            f'max_count ({new_max_count}) cannot be less than '
                            f'used_count ({used_count}).'
                        ),
                    },
                )

        effective_max_count = (
            new_max_count
            if new_max_count is not None
            else getattr(self.instance, 'max_count', None)
        )

        min_c = business.constants.PROMO_COMMON_MIN_COUNT
        max_c = business.constants.PROMO_COMMON_MAX_COUNT
        if effective_max_count is not None and not (
            min_c <= effective_max_count <= max_c
        ):
            raise rest_framework.serializers.ValidationError(
                {
                    'max_count': (
                        f'Must be between {min_c} and {max_c} for COMMON mode.'
                    ),
                },
            )

    def _validate_unique(self, data):
        """
        Validations for UNIQUE promo mode.
        """

        if 'promo_common' in data and data['promo_common'] is not None:
            raise rest_framework.serializers.ValidationError(
                {'promo_common': 'This field is not allowed for UNIQUE mode.'},
            )

        if self.instance is None and not data.get('promo_unique'):
            raise rest_framework.serializers.ValidationError(
                {'promo_unique': 'This field is required for UNIQUE mode.'},
            )

        effective_max_count = data.get(
            'max_count',
            getattr(self.instance, 'max_count', None),
        )

        if (
            effective_max_count is not None
            and effective_max_count
            != business.constants.PROMO_UNIQUE_MAX_COUNT
        ):
            raise rest_framework.serializers.ValidationError(
                {
                    'max_count': (
                        'Must be equal to '
                        f'{business.constants.PROMO_UNIQUE_MAX_COUNT} '
                        'for UNIQUE mode.'
                    ),
                },
            )

    def to_representation(self, instance):
        """
        Controls the display of fields in the response.
        """

        data = super().to_representation(instance)

        if not instance.image_url:
            data.pop('image_url', None)

        if instance.mode == business.constants.PROMO_MODE_UNIQUE:
            data.pop('promo_common', None)
            if 'promo_unique' in self.fields and isinstance(
                self.fields['promo_unique'],
                rest_framework.serializers.SerializerMethodField,
            ):
                data['promo_unique'] = self.get_promo_unique(instance)
            else:
                data['promo_unique'] = [
                    code.code for code in instance.unique_codes.all()
                ]
        else:
            data.pop('promo_unique', None)

        return data


class PromoCreateSerializer(BasePromoSerializer):
    url = rest_framework.serializers.HyperlinkedIdentityField(
        view_name='api-business:promo-detail',
        lookup_field='id',
    )

    class Meta(BasePromoSerializer.Meta):
        fields = ('url',) + BasePromoSerializer.Meta.fields

    def create(self, validated_data):
        target_data = validated_data.pop('target')
        promo_common = validated_data.pop('promo_common', None)
        promo_unique = validated_data.pop('promo_unique', None)

        return business.models.Promo.objects.create_promo(
            user=self.context['request'].user,
            target_data=target_data,
            promo_common=promo_common,
            promo_unique=promo_unique,
            **validated_data,
        )


class PromoListQuerySerializer(
    core.serializers.BaseLimitOffsetPaginationSerializer,
):
    """
    Validates query parameters for the list of promotions.
    """

    sort_by = rest_framework.serializers.ChoiceField(
        choices=['active_from', 'active_until'],
        required=False,
    )
    country = MultiCountryField(required=False)

    def validate(self, attrs):
        query_params = self.initial_data.keys()
        allowed_params = self.fields.keys()
        unexpected_params = set(query_params) - set(allowed_params)

        if unexpected_params:
            raise rest_framework.exceptions.ValidationError(
                f'Invalid parameters: {", ".join(unexpected_params)}',
            )

        if 'country' in attrs:
            attrs['countries'] = attrs.pop('country')

        return attrs


class PromoDetailSerializer(BasePromoSerializer):
    promo_id = rest_framework.serializers.UUIDField(
        source='id',
        read_only=True,
    )
    company_name = rest_framework.serializers.CharField(
        source='company.name',
        read_only=True,
    )
    like_count = rest_framework.serializers.IntegerField(
        source='get_like_count',
        read_only=True,
    )
    comment_count = rest_framework.serializers.IntegerField(
        source='get_comment_count',
        read_only=True,
    )
    used_count = rest_framework.serializers.IntegerField(
        source='get_used_codes_count',
        read_only=True,
    )
    active = rest_framework.serializers.BooleanField(
        source='is_active',
        read_only=True,
    )

    promo_unique = rest_framework.serializers.SerializerMethodField()

    class Meta(BasePromoSerializer.Meta):
        fields = BasePromoSerializer.Meta.fields + (
            'promo_id',
            'company_name',
            'like_count',
            'comment_count',
            'used_count',
            'active',
        )

    def get_promo_unique(self, obj):
        if obj.mode == business.constants.PROMO_MODE_UNIQUE:
            return obj.get_available_unique_codes
        return None

    def update(self, instance, validated_data):
        target_data = validated_data.pop('target', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if target_data is not None:
            instance.target = target_data

        instance.save()
        return instance


class PromoReadOnlySerializer(PromoDetailSerializer):
    """Read-only serializer for promo."""

    company_id = rest_framework.serializers.UUIDField(
        source='company.id',
        read_only=True,
    )

    class Meta(PromoDetailSerializer.Meta):
        fields = PromoDetailSerializer.Meta.fields + ('company_id',)
        read_only_fields = fields


class CountryStatSerializer(rest_framework.serializers.Serializer):
    """Serializer for activation statistics by country."""

    country = rest_framework.serializers.CharField()
    activations_count = rest_framework.serializers.IntegerField()


class PromoStatSerializer(rest_framework.serializers.Serializer):
    """Serializer for overall promo code statistics."""

    activations_count = rest_framework.serializers.IntegerField()
    countries = CountryStatSerializer(many=True)
