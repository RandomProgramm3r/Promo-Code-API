import django.urls
import rest_framework
import rest_framework.status
import rest_framework.test

import business.models


class BaseBusinessAuthTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.company_refresh_url = django.urls.reverse(
            'api-business:company-token-refresh',
        )
        cls.protected_url = django.urls.reverse('api-core:protected')
        cls.signup_url = django.urls.reverse('api-business:company-sign-up')
        cls.signin_url = django.urls.reverse('api-business:company-sign-in')
        cls.valid_data = {
            'name': 'Digital Marketing Solutions Inc.',
            'email': 'testcompany@example.com',
            'password': 'SecurePass123!',
        }

    def tearDown(self):
        business.models.Company.objects.all().delete()
