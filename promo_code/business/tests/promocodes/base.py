import django.urls
import rest_framework
import rest_framework.status
import rest_framework.test

import business.models


class BasePromoCreateTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.promo_create_url = django.urls.reverse('api-business:promo-create')
        cls.signup_url = django.urls.reverse('api-business:company-sign-up')
        cls.signin_url = django.urls.reverse('api-business:company-sign-in')
        cls.valid_data = {
            'name': 'Digital Marketing Solutions Inc.',
            'email': 'testcompany@example.com',
            'password': 'SecurePass123!',
        }
        business.models.Company.objects.create_company(
            name=cls.valid_data['name'],
            email=cls.valid_data['email'],
            password=cls.valid_data['password'],
        )

        response = cls.client.post(
            cls.signin_url,
            {
                'email': cls.valid_data['email'],
                'password': cls.valid_data['password'],
            },
            format='json',
        )
        cls.token = response.data['access']

    def tearDown(self):
        business.models.Company.objects.all().delete()
        business.models.Promo.objects.all().delete()
        business.models.PromoCode.objects.all().delete()
