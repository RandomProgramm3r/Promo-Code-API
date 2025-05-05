import django.urls
import rest_framework.test
import rest_framework_simplejwt.token_blacklist.models as tb_models

import user.models


class BaseUserAuthTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.protected_url = django.urls.reverse('api-core:protected')
        cls.refresh_url = django.urls.reverse('api-user:user-token-refresh')
        cls.signup_url = django.urls.reverse('api-user:sign-up')
        cls.signin_url = django.urls.reverse('api-user:sign-in')

    def tearDown(self):
        user.models.User.objects.all().delete()
        tb_models.BlacklistedToken.objects.all().delete()
        tb_models.OutstandingToken.objects.all().delete()
        super().tearDown()
