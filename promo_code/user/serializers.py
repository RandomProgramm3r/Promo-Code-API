import django.contrib.auth.password_validation
import django.core.exceptions
import django.core.validators
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.serializers
import rest_framework_simplejwt.token_blacklist.models as tb_models
import rest_framework_simplejwt.tokens

import user.models as user_models
import user.validators


class SignUpSerializer(rest_framework.serializers.ModelSerializer):
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        max_length=60,
        min_length=8,
        style={'input_type': 'password'},
    )
    name = rest_framework.serializers.CharField(required=True, min_length=1)
    surname = rest_framework.serializers.CharField(required=True, min_length=1)
    email = rest_framework.serializers.EmailField(
        required=True,
        min_length=8,
        validators=[
            user.validators.UniqueEmailValidator(
                'This email address is already registered.',
                'email_conflict',
            ),
        ],
    )
    avatar_url = rest_framework.serializers.CharField(
        required=False,
        max_length=350,
        validators=[
            django.core.validators.URLValidator(schemes=['http', 'https']),
        ],
    )
    other = rest_framework.serializers.JSONField(
        required=True,
        validators=[user.validators.OtherFieldValidator()],
    )

    class Meta:
        model = user_models.User
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
            user = user_models.User.objects.create_user(
                email=validated_data['email'],
                name=validated_data['name'],
                surname=validated_data['surname'],
                avatar_url=validated_data.get('avatar_url'),
                other=validated_data['other'],
                password=validated_data['password'],
            )
            user.token_version += 1
            user.save()
            return user
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

        self.update_token_version(user)

        data = super().validate(attrs)

        refresh = rest_framework_simplejwt.tokens.RefreshToken(data['refresh'])

        self.invalidate_previous_tokens(user, refresh['jti'])

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

    def invalidate_previous_tokens(self, user, current_jti):
        outstanding_tokens = tb_models.OutstandingToken.objects.filter(
            user=user,
        ).exclude(jti=current_jti)

        for token in outstanding_tokens:
            tb_models.BlacklistedToken.objects.get_or_create(token=token)

    def update_token_version(self, user):
        user.token_version += 1
        user.save()

    def get_token(self, user):
        token = super().get_token(user)
        token['token_version'] = user.token_version
        return token
