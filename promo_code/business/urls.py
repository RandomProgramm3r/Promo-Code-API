import django.urls

import business.views

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
    django.urls.path(
        'token/refresh',
        business.views.CompanyTokenRefreshView.as_view(),
        name='company-token-refresh',
    ),
    django.urls.path(
        'promo',
        business.views.CompanyPromoListCreateView.as_view(),
        name='promo-list-create',
    ),
    django.urls.path(
        'promo/<uuid:id>',
        business.views.CompanyPromoDetailView.as_view(),
        name='promo-detail',
    ),
    django.urls.path(
        'promo/<uuid:id>/stat',
        business.views.CompanyPromoStatAPIView.as_view(),
        name='promo-statistics',
    ),
]
