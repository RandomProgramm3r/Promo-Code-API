import business.views
import django.urls

app_name = 'api-business'


urlpatterns = [
    django.urls.path(
        'auth/sign-up',
        business.views.CompanySignUpView.as_view(),
        name='company-sign-up',
    ),
    django.urls.path(
        'auth/sign-in',
        business.views.CompanySignInView.as_view(),
        name='company-sign-in',
    ),
]
