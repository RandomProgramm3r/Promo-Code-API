import rest_framework.exceptions
import rest_framework.generics
import rest_framework.response
import rest_framework.serializers
import rest_framework.status
import rest_framework_simplejwt.tokens
import rest_framework_simplejwt.views

import user.serializers


class SignUpView(rest_framework.generics.CreateAPIView):
    serializer_class = user.serializers.SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except rest_framework.exceptions.ValidationError as e:
            if hasattr(e, 'get_codes'):
                codes = e.get_codes()
                if 'email' in codes and 'email_conflict' in codes['email']:
                    return rest_framework.response.Response(
                        {
                            'status': 'error',
                            'message': (
                                'This email address is already registered.'
                            ),
                        },
                        status=rest_framework.status.HTTP_409_CONFLICT,
                    )

            return rest_framework.response.Response(
                {'status': 'error', 'message': 'Error in request data.'},
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(user)
        return rest_framework.response.Response(
            {'token': str(refresh.access_token)},
            status=rest_framework.status.HTTP_200_OK,
        )


class SignInView(rest_framework_simplejwt.views.TokenViewBase):
    serializer_class = user.serializers.SignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except rest_framework.serializers.ValidationError as e:
            code = (
                next(iter(e.get_codes().values()))[0]
                if e.get_codes()
                else None
            )
            if code == 'authorization':
                return rest_framework.response.Response(
                    {
                        'status': 'error',
                        'message': 'Invalid email or password.',
                    },
                    status=rest_framework.status.HTTP_401_UNAUTHORIZED,
                )

            return rest_framework.response.Response(
                {'status': 'error', 'message': 'Error in request data.'},
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        return rest_framework.response.Response(
            serializer.get_token(),
            status=rest_framework.status.HTTP_200_OK,
        )
