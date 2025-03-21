import rest_framework_simplejwt.authentication
import rest_framework_simplejwt.exceptions


class CustomJWTAuthentication(
    rest_framework_simplejwt.authentication.JWTAuthentication,
):
    def authenticate(self, request):
        try:
            user_token = super().authenticate(request)
        except rest_framework_simplejwt.exceptions.InvalidToken:
            raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                'Token is invalid or expired',
            )

        if user_token:
            user, token = user_token
            if token.payload.get('token_version') != user.token_version:
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    'Token invalid',
                )

        return user_token
