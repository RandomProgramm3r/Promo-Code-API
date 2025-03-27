import django.urls
import rest_framework_simplejwt.views

import user.views

app_name = 'api-user'


urlpatterns = [
    django.urls.path(
        'auth/sign-up',
        user.views.SignUpView.as_view(),
        name='sign-up',
    ),
    django.urls.path(
        'auth/sign-in',
        rest_framework_simplejwt.views.TokenObtainPairView.as_view(),
        name='sign-in',
    ),
    django.urls.path(
        'token/refresh/',
        rest_framework_simplejwt.views.TokenRefreshView.as_view(),
        name='user-token-refresh',
    ),
]
