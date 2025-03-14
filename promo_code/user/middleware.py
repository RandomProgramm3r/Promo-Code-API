import django.http
import rest_framework_simplejwt.authentication


class TokenVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = rest_framework_simplejwt.authentication.JWTAuthentication()
        auth_result = auth.authenticate(request)

        if auth_result is None:
            return self.get_response(request)

        user, token = auth_result
        if user:
            token_version = token.payload.get('token_version', 0)
            if token_version != user.token_version:
                return django.http.JsonResponse(
                    {'error': 'Token invalid'},
                    status=401,
                )

        return self.get_response(request)
