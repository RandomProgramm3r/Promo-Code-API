import core.views
import django.urls

app_name = 'core'


urlpatterns = [
    django.urls.path(
        '',
        core.views.PingView.as_view(),
        name='ping',
    ),
]
