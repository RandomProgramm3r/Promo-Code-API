import django.contrib.auth.password_validation
import django.core.exceptions
import rest_framework.serializers
import rest_framework_simplejwt.tokens

import user.models


class SignUpSerializer(rest_framework.serializers.ModelSerializer):
    password = rest_framework.serializers.CharField(
        write_only=True,
        required=True,
        validators=[django.contrib.auth.password_validation.validate_password],
        max_length=60,
        min_length=8,
        style={'input_type': 'password'},
    )
    name = rest_framework.serializers.CharField(
        required=True,
    )
    surname = rest_framework.serializers.CharField(
        required=True,
    )
    email = rest_framework.serializers.EmailField(
        required=True,
    )
    other = rest_framework.serializers.JSONField(
        required=True,
    )

    class Meta:
        model = user.models.User
        fields = [
            'name',
            'surname',
            'email',
            'avatar_url',
            'other',
            'password',
        ]
        extra_kwargs = {'avatar_url': {'required': False}}

    def validate_email(self, value):
        if user.models.User.objects.filter(email=value).exists():
            raise rest_framework.serializers.ValidationError(
                'User with this email already exists.',
                code='email_conflict',
            )

        return value

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
            return user_
        except django.core.exceptions.ValidationError as e:
            raise rest_framework.serializers.ValidationError(e.messages)


class SignInSerializer(rest_framework.serializers.Serializer):
    email = rest_framework.serializers.EmailField(required=True)
    password = rest_framework.serializers.CharField(
        required=True,
        write_only=True,
    )

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise rest_framework.serializers.ValidationError(
                {'status': 'error', 'message': 'Both fields are required.'},
                code='required',
            )

        user = django.contrib.auth.authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )
        if not user:
            raise rest_framework.serializers.ValidationError(
                {'status': 'error', 'message': 'Invalid email or password.'},
                code='authorization',
            )

        data['user'] = user
        return data

    def get_token(self):
        user = self.validated_data['user']
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(user)
        return {'token': str(refresh.access_token)}
