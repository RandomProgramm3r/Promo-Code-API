import django.urls

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
        user.views.SignInView.as_view(),
        name='sign-in',
    ),
]
