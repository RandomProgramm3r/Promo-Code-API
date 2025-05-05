import django.urls
import rest_framework.test
import rest_framework_simplejwt.token_blacklist.models as tb_models

import business.models
import user.models


class BaseUserTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.signup_url = django.urls.reverse('api-user:sign-up')
        cls.signin_url = django.urls.reverse('api-user:sign-in')
        cls.user_profile_url = django.urls.reverse('api-user:user-profile')
        cls.promo_list_create_url = django.urls.reverse(
            'api-business:promo-list-create',
        )

        company1_data = {
            'name': 'Digital Marketing Solutions Inc.',
            'email': 'company1@example.com',
            'password': 'SecurePass123!',
        }
        business.models.Company.objects.create_company(**company1_data)
        cls.company1 = business.models.Company.objects.get(
            email=company1_data['email'],
        )
        response1 = cls.client.post(
            django.urls.reverse(
                'api-business:company-sign-in',
            ),
            {
                'email': company1_data['email'],
                'password': company1_data['password'],
            },
            format='json',
        )
        cls.company1_token = response1.data['access']

    def tearDown(self):
        business.models.Company.objects.all().delete()
        business.models.Promo.objects.all().delete()
        business.models.PromoCode.objects.all().delete()
        user.models.User.objects.all().delete()
        tb_models.BlacklistedToken.objects.all().delete()
        tb_models.OutstandingToken.objects.all().delete()
        super().tearDown()

    @classmethod
    def promo_detail_url(cls, promo_id):
        return django.urls.reverse(
            'api-user:user-promo-detail',
            kwargs={'id': promo_id},
        )
