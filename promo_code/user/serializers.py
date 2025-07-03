import django.contrib.auth.password_validation
import django.core.exceptions
import django.core.validators
import django.db.models
import pycountry
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.token_blacklist.models as tb_models
import rest_framework_simplejwt.tokens

import business.constants
import business.models
import user.constants
import user.models
import user.validators


class OtherFieldSerializer(rest_framework.serializers.Serializer):
    age = rest_framework.serializers.IntegerField(
        required=True,
        min_value=user.constants.AGE_MIN,
        max_value=user.constants.AGE_MAX,
    )
    country = rest_framework.serializers.CharField(
        required=True,
        max_length=user.constants.COUNTRY_CODE_LENGTH,
        min_length=user.constants.COUNTRY_CODE_LENGTH,
    )

    def validate(self, value):
        country = value['country']

        try:
            pycountry.countries.lookup(country.upper())
        except LookupError:
            raise rest_framework.serializers.ValidationError(
                'Invalid ISO 3166-1 alpha-2 country code.',
            )

        return value


class SignUpSerializer(rest_framework.serializers.ModelSerializer):
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        max_length=user.constants.PASSWORD_MAX_LENGTH,
        min_length=user.constants.PASSWORD_MIN_LENGTH,
        style={'input_type': 'password'},
    )
    name = rest_framework.serializers.CharField(
        required=True,
        min_length=user.constants.NAME_MIN_LENGTH,
        max_length=user.constants.NAME_MAX_LENGTH,
    )
    surname = rest_framework.serializers.CharField(
        required=True,
        min_length=user.constants.SURNAME_MIN_LENGTH,
        max_length=user.constants.SURNAME_MAX_LENGTH,
    )
    email = rest_framework.serializers.EmailField(
        required=True,
        min_length=user.constants.EMAIL_MIN_LENGTH,
        max_length=user.constants.EMAIL_MAX_LENGTH,
        validators=[
            user.validators.UniqueEmailValidator(
                'This email address is already registered.',
                'email_conflict',
            ),
        ],
    )
    avatar_url = rest_framework.serializers.CharField(
        required=False,
        max_length=user.constants.AVATAR_URL_MAX_LENGTH,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    other = OtherFieldSerializer(required=True)

    class Meta:
        model = user.models.User
        fields = (
            'name',
            'surname',
            'email',
            'avatar_url',
            'other',
            'password',
        )

    def create(self, validated_data):
        try:
            user_ = user.models.User.objects.create_user(
                email=validated_data['email'],
                name=validated_data['name'],
                surname=validated_data['surname'],
                avatar_url=validated_data.get('avatar_url'),
                other=validated_data['other'],
                password=validated_data['password'],
            )
            user_.token_version += 1
            user_.save()
            return user_
        except django.core.exceptions.ValidationError as e:
            raise rest_framework.serializers.ValidationError(e.messages)


class SignInSerializer(
    rest_framework_simplejwt.serializers.TokenObtainPairSerializer,
):
    email = rest_framework.serializers.EmailField(required=True)
    password = rest_framework.serializers.CharField(
        required=True,
        write_only=True,
    )

    def validate(self, attrs):
        user = self.authenticate_user(attrs)

        user.token_version = django.db.models.F('token_version') + 1
        user.save(update_fields=['token_version'])

        data = super().validate(attrs)

        refresh = rest_framework_simplejwt.tokens.RefreshToken(data['refresh'])

        self.blacklist_other_tokens(user, refresh['jti'])

        return data

    def authenticate_user(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise rest_framework.exceptions.ValidationError(
                {'detail': 'Both email and password are required'},
                code='required',
            )

        user = django.contrib.auth.authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )

        if not user or not user.is_active:
            raise rest_framework.exceptions.AuthenticationFailed(
                {'detail': 'Invalid credentials or inactive account'},
                code='authentication_failed',
            )

        return user

    def blacklist_other_tokens(self, user, current_jti):
        qs = tb_models.OutstandingToken.objects.filter(user=user).exclude(
            jti=current_jti,
        )
        blacklisted = [tb_models.BlacklistedToken(token=tok) for tok in qs]
        tb_models.BlacklistedToken.objects.bulk_create(
            blacklisted,
            ignore_conflicts=True,
        )

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['token_version'] = user.token_version
        return token


class UserProfileSerializer(rest_framework.serializers.ModelSerializer):
    name = rest_framework.serializers.CharField(
        required=False,
        min_length=user.constants.NAME_MIN_LENGTH,
        max_length=user.constants.NAME_MAX_LENGTH,
    )
    surname = rest_framework.serializers.CharField(
        required=False,
        min_length=user.constants.SURNAME_MIN_LENGTH,
        max_length=user.constants.SURNAME_MAX_LENGTH,
    )
    email = rest_framework.serializers.EmailField(
        required=False,
        min_length=user.constants.EMAIL_MIN_LENGTH,
        max_length=user.constants.EMAIL_MAX_LENGTH,
        validators=[
            user.validators.UniqueEmailValidator(
                'This email address is already registered.',
                'email_conflict',
            ),
        ],
    )
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=False,
        validators=[django.contrib.auth.password_validation.validate_password],
        max_length=user.constants.PASSWORD_MAX_LENGTH,
        min_length=user.constants.PASSWORD_MIN_LENGTH,
        style={'input_type': 'password'},
    )
    avatar_url = rest_framework.serializers.CharField(
        required=False,
        max_length=user.constants.AVATAR_URL_MAX_LENGTH,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    other = OtherFieldSerializer(required=False)

    class Meta:
        model = user.models.User
        fields = (
            'name',
            'surname',
            'email',
            'password',
            'avatar_url',
            'other',
        )

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        if password:
            # do not invalidate the token
            instance.set_password(password)

        other_data = validated_data.pop('other', None)
        if other_data is not None:
            instance.other = other_data

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # If the response structure implies that a field is optional,
        # the server MUST NOT return the field if it is missing.
        if not instance.avatar_url:
            data.pop('avatar_url', None)
        return data


class UserFeedQuerySerializer(rest_framework.serializers.Serializer):
    """
    Serializer for validating query parameters of promo feed requests.
    """

    limit = rest_framework.serializers.CharField(
        required=False,
        allow_blank=True,
    )
    offset = rest_framework.serializers.CharField(
        required=False,
        allow_blank=True,
    )
    category = rest_framework.serializers.CharField(
        min_length=business.constants.TARGET_CATEGORY_MIN_LENGTH,
        max_length=business.constants.TARGET_CATEGORY_MAX_LENGTH,
        required=False,
        allow_blank=True,
    )
    active = rest_framework.serializers.BooleanField(
        required=False,
        allow_null=True,
    )

    _allowed_params = None

    def get_allowed_params(self):
        if self._allowed_params is None:
            self._allowed_params = set(self.fields.keys())
        return self._allowed_params

    def validate(self, attrs):
        query_params = self.initial_data
        allowed_params = self.get_allowed_params()

        unexpected_params = set(query_params.keys()) - allowed_params
        if unexpected_params:
            raise rest_framework.exceptions.ValidationError('Invalid params.')

        field_errors = {}

        attrs = self._validate_int_field('limit', attrs, field_errors)
        attrs = self._validate_int_field('offset', attrs, field_errors)

        if field_errors:
            raise rest_framework.exceptions.ValidationError(field_errors)

        return attrs

    def validate_category(self, value):
        cotegory = self.initial_data.get('category')

        if cotegory is None:
            return value

        if value == '':
            raise rest_framework.exceptions.ValidationError(
                'Invalid category format.',
            )

        return value

    def _validate_int_field(self, field_name, attrs, field_errors):
        value_str = self.initial_data.get(field_name)
        if value_str is None:
            return attrs

        if value_str == '':
            raise rest_framework.exceptions.ValidationError(
                f'Invalid {field_name} format.',
            )

        try:
            value_int = int(value_str)
            if value_int < 0:
                raise rest_framework.exceptions.ValidationError(
                    f'{field_name.capitalize()} cannot be negative.',
                )
            attrs[field_name] = value_int
        except (ValueError, TypeError):
            raise rest_framework.exceptions.ValidationError(
                f'Invalid {field_name} format.',
            )

        return attrs


class PromoFeedSerializer(rest_framework.serializers.ModelSerializer):
    promo_id = rest_framework.serializers.UUIDField(source='id')
    company_id = rest_framework.serializers.UUIDField(source='company.id')
    company_name = rest_framework.serializers.CharField(source='company.name')
    active = rest_framework.serializers.BooleanField(source='is_active')
    is_activated_by_user = rest_framework.serializers.SerializerMethodField()
    like_count = rest_framework.serializers.IntegerField(
        source='get_like_count',
        read_only=True,
    )
    comment_count = rest_framework.serializers.IntegerField(
        source='get_comment_count',
        read_only=True,
    )
    is_liked_by_user = rest_framework.serializers.SerializerMethodField()

    class Meta:
        model = business.models.Promo
        fields = [
            'promo_id',
            'company_id',
            'company_name',
            'description',
            'image_url',
            'active',
            'is_activated_by_user',
            'like_count',
            'is_liked_by_user',
            'comment_count',
        ]

        read_only_fields = fields

    def get_is_liked_by_user(self, obj: business.models.Promo) -> bool:
        request = self.context.get('request')
        if (
            request
            and hasattr(request, 'user')
            and request.user.is_authenticated
        ):
            return user.models.PromoLike.objects.filter(
                promo=obj,
                user=request.user,
            ).exists()
        return False

    def get_is_activated_by_user(self, obj) -> bool:
        # TODO:
        return False


class UserPromoDetailSerializer(rest_framework.serializers.ModelSerializer):
    """
    Serializer for detailed promo-code information
    (without revealing the code value).
    The output format matches the given example.
    """

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
    active = rest_framework.serializers.BooleanField(
        source='is_active',
        read_only=True,
    )
    is_activated_by_user = rest_framework.serializers.SerializerMethodField()
    like_count = rest_framework.serializers.IntegerField(
        source='get_like_count',
        read_only=True,
    )
    comment_count = rest_framework.serializers.IntegerField(
        source='get_comment_count',
        read_only=True,
    )
    is_liked_by_user = rest_framework.serializers.SerializerMethodField()

    class Meta:
        model = business.models.Promo
        fields = (
            'promo_id',
            'company_id',
            'company_name',
            'description',
            'image_url',
            'active',
            'is_activated_by_user',
            'like_count',
            'comment_count',
            'is_liked_by_user',
        )
        read_only_fields = fields

    def get_is_liked_by_user(self, obj: business.models.Promo) -> bool:
        request = self.context.get('request')
        if (
            request
            and hasattr(request, 'user')
            and request.user.is_authenticated
        ):
            return user.models.PromoLike.objects.filter(
                promo=obj,
                user=request.user,
            ).exists()
        return False

    def get_is_activated_by_user(self, obj: business.models.Promo) -> bool:
        """
        Checks whether the current user has activated this promo code.
        """
        request = self.context.get('request')
        if not (
            request
            and hasattr(request, 'user')
            and request.user.is_authenticated
        ):
            return False

        return user.models.PromoActivationHistory.objects.filter(
            promo=obj,
            user=request.user,
        ).exists()


class UserAuthorSerializer(rest_framework.serializers.ModelSerializer):
    name = rest_framework.serializers.CharField(
        read_only=True,
        min_length=1,
        max_length=100,
    )
    surname = rest_framework.serializers.CharField(
        read_only=True,
        min_length=1,
        max_length=120,
    )
    avatar_url = rest_framework.serializers.URLField(
        read_only=True,
        max_length=350,
        allow_null=True,
    )

    class Meta:
        model = user.models.User
        fields = ('name', 'surname', 'avatar_url')


class CommentSerializer(rest_framework.serializers.ModelSerializer):
    id = rest_framework.serializers.UUIDField(read_only=True)
    text = rest_framework.serializers.CharField(
        min_length=user.constants.COMMENT_TEXT_MIN_LENGTH,
        max_length=user.constants.COMMENT_TEXT_MAX_LENGTH,
    )
    date = rest_framework.serializers.DateTimeField(
        source='created_at',
        read_only=True,
        format='%Y-%m-%dT%H:%M:%S%z',
    )
    author = UserAuthorSerializer(read_only=True)

    class Meta:
        model = user.models.PromoComment
        fields = ('id', 'text', 'date', 'author')


class CommentCreateSerializer(rest_framework.serializers.ModelSerializer):
    text = rest_framework.serializers.CharField(
        min_length=user.constants.COMMENT_TEXT_MIN_LENGTH,
        max_length=user.constants.COMMENT_TEXT_MAX_LENGTH,
    )

    class Meta:
        model = user.models.PromoComment
        fields = ('text',)


class CommentUpdateSerializer(rest_framework.serializers.ModelSerializer):
    text = rest_framework.serializers.CharField(
        min_length=user.constants.COMMENT_TEXT_MIN_LENGTH,
        max_length=user.constants.COMMENT_TEXT_MAX_LENGTH,
    )

    class Meta:
        model = user.models.PromoComment
        fields = ('text',)


class PromoActivationSerializer(rest_framework.serializers.Serializer):
    """
    Serializer for the response upon successful activation.
    """

    promo = rest_framework.serializers.CharField()
