import datetime

import rest_framework.exceptions
import rest_framework_simplejwt.authentication


class CustomJWTAuthentication(
    rest_framework_simplejwt.authentication.JWTAuthentication,
):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        last_login_str = validated_token.get('last_login')
        if last_login_str:
            last_login = datetime.datetime.fromisoformat(last_login_str)
            if user.last_login and user.last_login > last_login:
                raise rest_framework.exceptions.AuthenticationFailed(
                    'Token has been invalidated',
                )

        return user
