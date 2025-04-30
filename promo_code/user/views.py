import rest_framework.generics
import rest_framework.response
import rest_framework.status
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import user.serializers


class UserSignUpView(
    rest_framework.generics.CreateAPIView,
):
    serializer_class = user.serializers.SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version

        access_token = refresh.access_token

        response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
        }

        return rest_framework.response.Response(
            response_data,
            status=rest_framework.status.HTTP_200_OK,
        )


class UserSignInView(
    rest_framework_simplejwt.views.TokenObtainPairView,
):
    serializer_class = user.serializers.SignInSerializer
