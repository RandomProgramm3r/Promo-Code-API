import django.views
import django.http


class PingView(django.views.View):
    def get(self, request, *args, **kwargs):
        return django.http.HttpResponse('PROOOOOOOOOOOOOOOOOD', status=200)
