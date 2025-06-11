import django.urls
import rest_framework_simplejwt.views

import user.views

app_name = 'api-user'


urlpatterns = [
    django.urls.path(
        'auth/sign-up',
        user.views.UserSignUpView.as_view(),
        name='user-sign-up',
    ),
    django.urls.path(
        'auth/sign-in',
        user.views.UserSignInView.as_view(),
        name='user-sign-in',
    ),
    django.urls.path(
        'token/refresh/',
        rest_framework_simplejwt.views.TokenRefreshView.as_view(),
        name='user-token-refresh',
    ),
    django.urls.path(
        'profile',
        user.views.UserProfileView.as_view(),
        name='user-profile',
    ),
    django.urls.path(
        'feed',
        user.views.UserFeedView.as_view(),
        name='user-feed',
    ),
    django.urls.path(
        'promo/<uuid:id>',
        user.views.UserPromoDetailView.as_view(),
        name='user-promo-detail',
    ),
    django.urls.path(
        'promo/<uuid:id>/like',
        user.views.UserPromoLikeView.as_view(),
        name='user-promo-like',
    ),
    django.urls.path(
        'promo/<uuid:promo_id>/comments',
        user.views.PromoCommentListCreateView.as_view(),
        name='user-promo-comment-list-create',
    ),
    django.urls.path(
        'promo/<uuid:promo_id>/comments/<uuid:comment_id>',
        user.views.PromoCommentDetailView.as_view(),
        name='user-promo-comment-detail',
    ),
]
