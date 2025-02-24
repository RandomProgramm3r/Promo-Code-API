import django.urls

import core.views


app_name = 'core'


urlpatterns = [
    django.urls.path(
        '',
        core.views.PingView.as_view(),
        name='ping',
    ),
]