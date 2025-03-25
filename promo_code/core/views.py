import django.http
import django.views
import rest_framework.permissions
import rest_framework.response
import rest_framework.status
import rest_framework.views


class BaseCustomResponseMixin:
    error_response = {'status': 'error', 'message': 'Error in request data.'}

    def handle_validation_error(self):
        return rest_framework.response.Response(
            self.error_response,
            status=rest_framework.status.HTTP_400_BAD_REQUEST,
        )


class PingView(django.views.View):
    def get(self, request, *args, **kwargs):
        return django.http.HttpResponse('PROOOOOOOOOOOOOOOOOD', status=200)


class MyProtectedView(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get(self, request, format=None):
        content = {'status': 'request was permitted'}
        return rest_framework.response.Response(content)
