import django.http
import django.views
import rest_framework.permissions
import rest_framework.response
import rest_framework.views


class PingView(django.views.View):
    def get(self, request, *args, **kwargs):
        return django.http.HttpResponse('PROOOOOOOOOOOOOOOOOD', status=200)


class MyProtectedView(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get(self, request, format=None):
        content = {'status': 'request was permitted'}
        return rest_framework.response.Response(content)
