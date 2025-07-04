import django.conf
import django.core.cache
import django.urls
import django_redis
import rest_framework.test
import rest_framework_simplejwt.token_blacklist.models as tb_models

import business.models
import user.models


class BaseUserTestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        cls.user_signup_url = django.urls.reverse('api-user:user-sign-up')
        cls.user_signin_url = django.urls.reverse('api-user:user-sign-in')
        cls.user_profile_url = django.urls.reverse('api-user:user-profile')
        cls.user_feed_url = django.urls.reverse('api-user:user-feed')
        cls.user_promo_history_url = django.urls.reverse(
            'api-user:user-promo-history',
        )
        cls.company_signin_url = django.urls.reverse(
            'api-business:company-sign-in',
        )
        cls.promo_list_create_url = django.urls.reverse(
            'api-business:promo-list-create',
        )
        cls.antifraud_update_user_verdict_url = (
            django.conf.settings.ANTIFRAUD_UPDATE_USER_VERDICT_URL
        )
        cls.antifraud_set_delay_url = (
            django.conf.settings.ANTIFRAUD_SET_DELAY_URL
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
            cls.company_signin_url,
            {
                'email': company1_data['email'],
                'password': company1_data['password'],
            },
            format='json',
        )
        cls.company1_token = response1.data['access']
        cls.company1_name = cls.company1.name

        company2_data = {
            'name': 'Synergy Solutions Co.',
            'email': 'company2@example.com',
            'password': 'AnotherSecurePass456!',
        }
        business.models.Company.objects.create_company(**company2_data)

        cls.company2 = business.models.Company.objects.get(
            email=company2_data['email'],
        )
        response2 = cls.client.post(
            cls.company_signin_url,
            {
                'email': company2_data['email'],
                'password': company2_data['password'],
            },
            format='json',
        )
        cls.company2_token = response2.data['access']
        cls.company2_name = cls.company2.name

    def tearDown(self):
        business.models.Company.objects.all().delete()
        business.models.Promo.objects.all().delete()
        business.models.PromoCode.objects.all().delete()
        user.models.PromoActivationHistory.objects.all().delete()
        user.models.PromoComment.objects.all().delete()
        user.models.PromoLike.objects.all().delete()
        user.models.User.objects.all().delete()
        tb_models.BlacklistedToken.objects.all().delete()
        django_redis.get_redis_connection('default').flushall()
        super().tearDown()

    @classmethod
    def get_business_promo_detail_url(cls, promo_id):
        return django.urls.reverse(
            'api-business:promo-detail',
            kwargs={'id': promo_id},
        )

    @classmethod
    def get_user_promo_detail_url(cls, promo_id):
        return django.urls.reverse(
            'api-user:user-promo-detail',
            kwargs={'id': promo_id},
        )

    @classmethod
    def get_user_promo_activate_url(cls, promo_id):
        return django.urls.reverse(
            'api-user:user-promo-activate',
            kwargs={'id': promo_id},
        )

    @classmethod
    def get_user_promo_like_url(cls, promo_id):
        return django.urls.reverse(
            'api-user:user-promo-like',
            kwargs={'id': promo_id},
        )
