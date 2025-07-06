import django.urls
import rest_framework.status
import rest_framework.test

import business.models
import user.models
import user.tests.user.base


class BusinessPromoStatsTests(user.tests.user.base.BaseUserTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = rest_framework.test.APIClient()
        user1_data = {
            'name': 'Stephen',
            'surname': 'Woz',
            'email': 'steve2@example.com',
            'password': 'Californi@2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        response = cls.client.post(
            cls.user_signup_url,
            user1_data,
            format='json',
        )
        assert response.status_code == rest_framework.status.HTTP_200_OK
        cls.user1_token = response.data['access']

        user2_data = {
            'name': 'Michael',
            'surname': 'Bloom',
            'email': 'mike2@example.com',
            'password': 'Californi@2000!',
            'other': {'age': 15, 'country': 'us'},
        }
        response = cls.client.post(
            cls.user_signup_url,
            user2_data,
            format='json',
        )
        assert response.status_code == rest_framework.status.HTTP_200_OK
        cls.user2_token = response.data['access']

        user3_data = {
            'name': 'Yefim',
            'surname': 'Dinit',
            'email': 'yefim3@example.com',
            'password': 'StrongPass1!',
            'other': {'age': 40, 'country': 'kz'},
        }
        response = cls.client.post(
            cls.user_signup_url,
            user3_data,
            format='json',
        )
        assert response.status_code == rest_framework.status.HTTP_200_OK
        cls.user3_token = response.data['access']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company1_token,
        )
        promo_data = {
            'description': 'Stats Test Promotion',
            'target': {},
            'max_count': 20,
            'active_from': '2025-01-01',
            'mode': 'COMMON',
            'promo_common': 'stats-sale',
        }
        response = cls.client.post(
            cls.promo_list_create_url,
            promo_data,
            format='json',
        )
        assert response.status_code == rest_framework.status.HTTP_201_CREATED
        cls.promo_id = response.data['id']

        promo_instance = business.models.Promo.objects.get(id=cls.promo_id)
        user_1 = user.models.User.objects.get(email=user1_data['email'])
        user_2 = user.models.User.objects.get(email=user2_data['email'])
        user_3 = user.models.User.objects.get(email=user3_data['email'])
        for _ in range(3):
            user.models.PromoActivationHistory.objects.create(
                user=user_1,
                promo=promo_instance,
            )
        for _ in range(2):
            user.models.PromoActivationHistory.objects.create(
                user=user_2,
                promo=promo_instance,
            )
        for _ in range(4):
            user.models.PromoActivationHistory.objects.create(
                user=user_3,
                promo=promo_instance,
            )

    def setUp(self):
        super().setUp()
        self.client = rest_framework.test.APIClient()

    def test_stats_access_denied_for_other_company(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = django.urls.reverse(
            'api-business:promo-statistics',
            kwargs={'id': self.promo_id},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_get_activation_statistics(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        url = django.urls.reverse(
            'api-business:promo-statistics',
            kwargs={'id': self.promo_id},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(data['activations_count'], 9)
        counts = [item['activations_count'] for item in data['countries']]
        self.assertListEqual(counts, [3, 4, 2])
