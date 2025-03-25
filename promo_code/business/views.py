import business.models
import business.serializers
import rest_framework.exceptions
import rest_framework.generics
import rest_framework.response
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import core.views


class CompanySignUpView(
    core.views.BaseCustomResponseMixin,
    rest_framework.generics.CreateAPIView,
):
    def post(self, request):
        try:
            serializer = business.serializers.CompanySignUpSerializer(
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
        except (
            rest_framework.serializers.ValidationError,
            rest_framework_simplejwt.exceptions.TokenError,
        ) as e:
            if isinstance(e, rest_framework.serializers.ValidationError):
                return self.handle_validation_error()

            raise rest_framework_simplejwt.exceptions.InvalidToken(str(e))

        company = serializer.save()

        refresh = rest_framework_simplejwt.tokens.RefreshToken()
        refresh['user_type'] = 'company'
        refresh['company_id'] = company.id
        refresh['token_version'] = company.token_version

        access_token = refresh.access_token
        access_token['user_type'] = 'company'
        access_token['company_id'] = company.id
        refresh['token_version'] = company.token_version

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )


class CompanySignInView(
    core.views.BaseCustomResponseMixin,
    rest_framework_simplejwt.views.TokenObtainPairView,
):
    def post(self, request):
        try:
            serializer = business.serializers.CompanySignInSerializer(
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
        except (
            rest_framework.serializers.ValidationError,
            rest_framework_simplejwt.exceptions.TokenError,
        ) as e:
            if isinstance(e, rest_framework.serializers.ValidationError):
                return self.handle_validation_error()

            raise rest_framework_simplejwt.exceptions.InvalidToken(str(e))

        company = business.models.Company.objects.get(
            email=serializer.validated_data['email'],
        )
        company.token_version += 1
        company.save()

        refresh = rest_framework_simplejwt.tokens.RefreshToken()
        refresh['user_type'] = 'company'
        refresh['company_id'] = company.id
        refresh['token_version'] = company.token_version

        access_token = refresh.access_token
        access_token['user_type'] = 'company'
        access_token['company_id'] = company.id

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )
