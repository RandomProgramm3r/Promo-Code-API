import django.core.cache
import django.db.transaction
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.token_blacklist.models as tb_models
import rest_framework_simplejwt.tokens

import business.constants
import core.serializers
import core.utils.auth
import user.models


class SignUpSerializer(core.serializers.BaseUserSerializer):
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


class UserProfileSerializer(core.serializers.BaseUserSerializer):
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
        django.core.cache.cache.delete(
            f'auth_instance_{user_type}_{instance.id}_v{token_version}',
        )


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


class PromoFeedSerializer(core.serializers.BaseUserPromoSerializer):
    """
    Serializer for representing promo feed data for a user.
    """

    pass


class UserPromoDetailSerializer(core.serializers.BaseUserPromoSerializer):
    """
    Serializer for detailed promo-code information
    (without revealing the code value).
    The output format matches the given example.
    """

    pass


class UserAuthorSerializer(core.serializers.BaseUserSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta(core.serializers.BaseUserSerializer.Meta):
        fields = ('name', 'surname', 'avatar_url')
        read_only_fields = fields


class CommentSerializer(core.serializers.BaseCommentSerializer):
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

    class Meta(core.serializers.BaseCommentSerializer.Meta):
        fields = core.serializers.BaseCommentSerializer.Meta.fields + (
            'id',
            'date',
            'author',
        )


class CommentCreateSerializer(core.serializers.BaseCommentSerializer):
    pass


class CommentUpdateSerializer(core.serializers.BaseCommentSerializer):
    pass


class PromoActivationSerializer(rest_framework.serializers.Serializer):
    """
    Serializer for the response upon successful activation.
    """

    promo = rest_framework.serializers.CharField()
