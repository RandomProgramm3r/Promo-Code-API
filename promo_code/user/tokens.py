import rest_framework_simplejwt.tokens


class CustomAccessToken(rest_framework_simplejwt.tokens.AccessToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token['last_login'] = user.last_login.isoformat()
        return token
