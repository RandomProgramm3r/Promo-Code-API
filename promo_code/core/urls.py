import core.views
import django.urls

app_name = 'api-core'


urlpatterns = [
    django.urls.path(
        '',
        core.views.PingView.as_view(),
        name='ping',
    ),
    django.urls.path(
        'protected-endpoint/',
        core.views.MyProtectedView.as_view(),
        name='protected',
    ),
]
