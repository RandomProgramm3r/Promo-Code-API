import django.http
import django.views


class PingView(django.views.View):
    def get(self, request, *args, **kwargs):
        return django.http.HttpResponse('PROOOOOOOOOOOOOOOOOD', status=200)
