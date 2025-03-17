import rest_framework.exceptions
import rest_framework.generics
import rest_framework.response
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import user.serializers


class BaseCustomResponseMixin:
    error_response = {'status': 'error', 'message': 'Error in request data.'}

    def handle_validation_error(self):
        return rest_framework.response.Response(
            self.error_response,
            status=rest_framework.status.HTTP_400_BAD_REQUEST,
        )


class SignUpView(
    BaseCustomResponseMixin,
    rest_framework.generics.CreateAPIView,
):
    serializer_class = user.serializers.SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except rest_framework.exceptions.ValidationError:
            return self.handle_validation_error()

        user = serializer.save()
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version
        access_token = refresh.access_token
        return rest_framework.response.Response(
            {'access': str(access_token), 'refresh': str(refresh)},
            status=rest_framework.status.HTTP_200_OK,
        )


class SignInView(
    BaseCustomResponseMixin,
    rest_framework_simplejwt.views.TokenObtainPairView,
):
    serializer_class = user.serializers.SignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            response = super().post(request, *args, **kwargs)
        except (
            rest_framework.serializers.ValidationError,
            rest_framework_simplejwt.exceptions.TokenError,
        ) as e:
            if isinstance(e, rest_framework.serializers.ValidationError):
                return self.handle_validation_error()

            raise rest_framework_simplejwt.exceptions.InvalidToken(str(e))

        return rest_framework.response.Response(
            response,
            status=rest_framework.status.HTTP_200_OK,
        )
