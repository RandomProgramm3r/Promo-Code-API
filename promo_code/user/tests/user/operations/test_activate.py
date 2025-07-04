import datetime

import requests
import rest_framework.status

import user.tests.user.base


class PromoActivationTests(user.tests.user.base.BaseUserTestCase):
    def setUp(self):
        super().setUp()

        user1_data = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator2@apple.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        response = self.client.post(
            self.user_signup_url,
            user1_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.user1_token = response.data['access']

        user2_data = {
            'name': 'Mike',
            'surname': 'Bloomberg',
            'email': 'mike2@bloomberg.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 15, 'country': 'us'},
        }
        response = self.client.post(
            self.user_signup_url,
            user2_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.user2_token = response.data['access']

        user3_data = {
            'name': 'Yefim',
            'surname': 'Dinitz',
            'email': 'algo3@prog.ru',
            'password': 'HardPASSword1!',
            'other': {'age': 40, 'country': 'kz'},
        }
        response = self.client.post(
            self.user_signup_url,
            user3_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.user3_token = response.data['access']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        promo1_data = {
            'description': 'Active COMMON promo for all',
            'target': {},
            'max_count': 4,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_list_create_url,
            promo1_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        self.promo1_id = response.data['id']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        promo2_data = {
            'description': 'Inactive COMMON promo for kz, 28..',
            'target': {'country': 'kz', 'age_from': 28},
            'max_count': 10,
            'active_from': (
                datetime.date.today() + datetime.timedelta(days=10)
            ).strftime(
                '%Y-%m-%d',
            ),
            'mode': 'COMMON',
            'promo_common': 'sale-20',
        }
        response = self.client.post(
            self.promo_list_create_url,
            promo2_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        self.promo2_id = response.data['id']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        promo3_data = {
            'description': 'Active UNIQUE promo for gb, 45..',
            'target': {'country': 'gb', 'age_from': 45},
            'active_until': '2035-02-10',
            'mode': 'UNIQUE',
            'max_count': 1,
            'promo_unique': ['uniq1', 'uniq2'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            promo3_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        self.promo3_id = response.data['id']

    def test_inactive_promo_activation_denied(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo2_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_targeting_mismatch_promo_activation_denied(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        promo_target_data = {
            'description': 'Active COMMON promo for us, 20..',
            'target': {'country': 'us', 'age_from': 20},
            'max_count': 10,
            'active_from': '2020-01-01',
            'mode': 'COMMON',
            'promo_common': 'target-sale',
        }
        response = self.client.post(
            self.promo_list_create_url,
            promo_target_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        promo_target_id = response.data['id']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(promo_target_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_common_promo_activation_by_user1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo'], 'sale-10')

    def test_common_promo_activation_by_user3(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo'], 'sale-10')

    def test_common_promo_multiple_activation_by_same_user(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo'], 'sale-10')
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo'], 'sale-10')

    def test_blocked_user_promo_activation_denied(self):
        self.client.credentials()
        response = requests.post(
            self.antifraud_update_user_verdict_url,
            json={'user_email': 'mike2@bloomberg.com', 'ok': False},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertNotIn('promo', response)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_common_promo_max_count_exhausted(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        for _ in range(2):
            response = self.client.post(
                self.get_user_promo_activate_url(self.promo1_id),
                format='json',
            )
            self.assertEqual(
                response.status_code,
                rest_framework.status.HTTP_200_OK,
            )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_patch_max_count_less_than_used_count_denied(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        patch_data = {'max_count': 0}
        response = self.client.patch(
            self.get_business_promo_detail_url(self.promo1_id),
            patch_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_unique_promo_activation_by_user1_first_attempt(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn(
            response.data['promo'],
            ['uniq1', 'uniq2'],
        )

    def test_unique_promo_activation_by_user1_denied_by_max_count(
        self,
    ):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_get_promo_detail_for_activated_promo_by_user1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo_id'], self.promo1_id)
        self.assertTrue(response.data['active'])
        self.assertTrue(response.data['is_activated_by_user'])
