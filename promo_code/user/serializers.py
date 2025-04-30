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
