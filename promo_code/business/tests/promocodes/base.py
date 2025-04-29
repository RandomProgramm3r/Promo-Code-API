import django.urls
import rest_framework
import rest_framework.status
import rest_framework.test

import business.models


class BasePromoTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.promo_list_create_url = django.urls.reverse(
            'api-business:promo-list-create',
        )
        cls.signup_url = django.urls.reverse('api-business:company-sign-up')
        cls.signin_url = django.urls.reverse('api-business:company-sign-in')

        cls.company1_data = {
            'name': 'Digital Marketing Solutions Inc.',
            'email': 'company1@example.com',
            'password': 'SecurePass123!',
        }
        business.models.Company.objects.create_company(**cls.company1_data)
        cls.company1 = business.models.Company.objects.get(
            email=cls.company1_data['email'],
        )

        cls.company2_data = {
            'name': 'Global Retail Hub LLC',
            'email': 'company2@example.com',
            'password': 'SecurePass456!',
        }
        business.models.Company.objects.create_company(**cls.company2_data)
        cls.company2 = business.models.Company.objects.get(
            email=cls.company2_data['email'],
        )

        response1 = cls.client.post(
            cls.signin_url,
            {
                'email': cls.company1_data['email'],
                'password': cls.company1_data['password'],
            },
            format='json',
        )
        cls.company1_token = response1.data['access']

        response2 = cls.client.post(
            cls.signin_url,
            {
                'email': cls.company2_data['email'],
                'password': cls.company2_data['password'],
            },
            format='json',
        )
        cls.company2_token = response2.data['access']

    @classmethod
    def promo_detail_url(cls, promo_id):
        return django.urls.reverse(
            'api-business:promo-detail',
            kwargs={'id': promo_id},
        )

    def tearDown(self):
        business.models.Company.objects.all().delete()
        business.models.Promo.objects.all().delete()
        business.models.PromoCode.objects.all().delete()
