import business.models as business_models
import business.validators
import django.contrib.auth.password_validation
import django.core.exceptions
import django.core.validators
import rest_framework.exceptions
import rest_framework.serializers
import rest_framework.status


class CompanySignUpSerializer(rest_framework.serializers.ModelSerializer):
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
