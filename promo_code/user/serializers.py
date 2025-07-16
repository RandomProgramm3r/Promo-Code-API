import django.contrib.auth.password_validation
import django.core.cache
import django.db.transaction
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.token_blacklist.models as tb_models
import rest_framework_simplejwt.tokens

import business.constants
import business.models
import core.serializers
import core.utils.auth
import user.constants
import user.models


class OtherFieldSerializer(rest_framework.serializers.Serializer):
    age = rest_framework.serializers.IntegerField(
        required=True,
        min_value=user.constants.AGE_MIN,
        max_value=user.constants.AGE_MAX,
    )
    country = core.serializers.CountryField(required=True)


class BaseUserSerializer(rest_framework.serializers.ModelSerializer):
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
    )
    avatar_url = rest_framework.serializers.URLField(
        required=False,
        max_length=user.constants.AVATAR_URL_MAX_LENGTH,
        allow_null=True,
    )
    other = OtherFieldSerializer(required=True)

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


class SignUpSerializer(BaseUserSerializer):

    @django.db.transaction.atomic
    def create(self, validated_data):
        try:
            user_ = user.models.User.objects.create_user(**validated_data)
        except django.db.IntegrityError:
            exc = rest_framework.exceptions.APIException(
                detail={
                    'email': 'This email address is already registered.',
                },
            )
            exc.status_code = 409
            raise exc

        return core.utils.auth.bump_token_version(user_)


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

        user = core.utils.auth.bump_token_version(user)

        self.user = user

        data = super().validate(attrs)

        refresh = data.get('refresh')
        if refresh:
            refresh_token = rest_framework_simplejwt.tokens.RefreshToken(
                refresh,
            )
            self.blacklist_other_tokens(user, refresh_token['jti'])

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


class UserProfileSerializer(BaseUserSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def validate_email(self, value):
        if (
            user.models.User.objects.filter(email=value)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise rest_framework.serializers.ValidationError(
                {'email': 'This email address is already registered.'},
            )
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        other_data = validated_data.pop('other', None)

        instance = super().update(instance, validated_data)

        if other_data is not None:
            instance.other.update(other_data)

        if password:
            instance.set_password(password)

        update_fields = []
        if other_data is not None:
            update_fields.append('other')
        if password:
            update_fields.append('password')

        if update_fields:
            instance.save(update_fields=update_fields)

        self._invalidate_cache(instance)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # If the response structure implies that a field is optional,
        # the server MUST NOT return the field if it is missing.
        if not instance.avatar_url:
            data.pop('avatar_url', None)
        return data

    def _invalidate_cache(self, instance):
        """
        Private helper to remove the authentication instance cache key.
        """

        user_type = instance.__class__.__name__.lower()
        token_version = getattr(instance, 'token_version', None)
        cache_key = f'auth_instance_{user_type}_{instance.id}_v{token_version}'
        django.core.cache.cache.delete(cache_key)


class UserFeedQuerySerializer(
    core.serializers.BaseLimitOffsetPaginationSerializer,
):
    """
    Serializer for validating query parameters of promo feed requests.
    """

    category = rest_framework.serializers.CharField(
        min_length=business.constants.TARGET_CATEGORY_MIN_LENGTH,
        max_length=business.constants.TARGET_CATEGORY_MAX_LENGTH,
        required=False,
        allow_blank=False,
    )
    active = rest_framework.serializers.BooleanField(
        required=False,
    )

    def validate(self, attrs):
        query_params = self.initial_data.keys()
        allowed_params = self.fields.keys()
        unexpected_params = set(query_params) - set(allowed_params)

        if unexpected_params:
            raise rest_framework.exceptions.ValidationError(
                f'Invalid parameters: {", ".join(unexpected_params)}',
            )

        if (
            'category' in self.initial_data
            and self.initial_data.get('category') == ''
        ):
            raise rest_framework.serializers.ValidationError(
                {'category': 'This field cannot be blank.'},
            )

        return attrs


class BaseUserPromoSerializer(rest_framework.serializers.ModelSerializer):
    """
    Base serializer for promos, containing common fields and methods.
    """

    promo_id = rest_framework.serializers.UUIDField(source='id')
    company_id = rest_framework.serializers.UUIDField(source='company.id')
    company_name = rest_framework.serializers.CharField(source='company.name')
    active = rest_framework.serializers.BooleanField(source='is_active')
    like_count = rest_framework.serializers.IntegerField(
        source='get_like_count',
    )
    comment_count = rest_framework.serializers.IntegerField(
        source='get_comment_count',
    )

    is_liked_by_user = rest_framework.serializers.SerializerMethodField()
    is_activated_by_user = rest_framework.serializers.SerializerMethodField()

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
        """
        Checks whether the current user has liked this promo.
        """
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


class PromoFeedSerializer(BaseUserPromoSerializer):
    """
    Serializer for representing promo feed data for a user.
    """

    pass


class UserPromoDetailSerializer(BaseUserPromoSerializer):
    """
    Serializer for detailed promo-code information
    (without revealing the code value).
    The output format matches the given example.
    """

    pass


class UserAuthorSerializer(BaseUserSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta(BaseUserSerializer.Meta):
        fields = ('name', 'surname', 'avatar_url')
        read_only_fields = fields


class BaseCommentSerializer(rest_framework.serializers.ModelSerializer):
    """
    Base serializer for promo comments.
    """

    text = rest_framework.serializers.CharField(
        min_length=user.constants.COMMENT_TEXT_MIN_LENGTH,
        max_length=user.constants.COMMENT_TEXT_MAX_LENGTH,
    )

    class Meta:
        model = user.models.PromoComment
        fields = ('text',)


class CommentSerializer(BaseCommentSerializer):
    """
    Serializer for displaying (reading) a comment.
    """

    id = rest_framework.serializers.UUIDField(read_only=True)
    date = rest_framework.serializers.DateTimeField(
        source='created_at',
        read_only=True,
        format='%Y-%m-%dT%H:%M:%S%z',
    )
    author = UserAuthorSerializer(read_only=True)

    class Meta(BaseCommentSerializer.Meta):
        fields = BaseCommentSerializer.Meta.fields + (
            'id',
            'date',
            'author',
        )


class CommentCreateSerializer(BaseCommentSerializer):
    pass


class CommentUpdateSerializer(BaseCommentSerializer):
    pass


class PromoActivationSerializer(rest_framework.serializers.Serializer):
    """
    Serializer for the response upon successful activation.
    """

    promo = rest_framework.serializers.CharField()
