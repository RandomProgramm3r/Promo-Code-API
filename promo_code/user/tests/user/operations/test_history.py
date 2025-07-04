import rest_framework.status

import user.models
import user.tests.user.base


class PromoHistoryTests(user.tests.user.base.BaseUserTestCase):
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
        self.user1 = user.models.User.objects.get(email=user1_data['email'])

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        promo1_data = {
            'description': 'Common promo for all',
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
        promo3_data = {
            'description': 'Unique promo for gb, 45..',
            'target': {'country': 'gb', 'age_from': 45},
            'active_until': '2035-02-10',
            'mode': 'UNIQUE',
            'max_count': 1,
            'promo_unique': ['unique-code-a', 'unique-code-b'],
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

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )

        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )

    def test_get_promo_history_for_user1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.get(self.user_promo_history_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        user.models.PromoActivationHistory.objects.filter(
            user=self.user1,
        ).delete()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )

        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )

        response = self.client.get(self.user_promo_history_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        expected_promo_ids_in_history = [
            self.promo3_id,
            self.promo3_id,
            self.promo1_id,
            self.promo1_id,
        ]

        self.assertEqual(
            len(response.data),
            len(expected_promo_ids_in_history),
        )
        for i, item in enumerate(response.data):
            self.assertEqual(
                item['promo_id'],
                expected_promo_ids_in_history[i],
            )
            self.assertFalse(
                item['active'],
            )
            self.assertTrue(item['is_activated_by_user'])

    def test_get_promo_history_with_pagination_offset_limit(self):
        user.models.PromoActivationHistory.objects.filter(
            user=self.user1,
        ).delete()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )

        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )

        expected_promo_ids = [self.promo1_id, self.promo1_id]

        response = self.client.get(
            self.user_promo_history_url,
            {'offset': 2, 'limit': 3},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]['promo_id'], expected_promo_ids[0])
        self.assertEqual(response.data[1]['promo_id'], expected_promo_ids[1])

        self.assertFalse(response.data[0]['active'])
        self.assertTrue(response.data[0]['is_activated_by_user'])
        self.assertFalse(response.data[1]['active'])
        self.assertTrue(response.data[1]['is_activated_by_user'])

        self.assertEqual(response.headers['X-Total-Count'], '4')

    def test_get_promo_history_with_zero_limit(self):
        user.models.PromoActivationHistory.objects.filter(
            user=self.user1,
        ).delete()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )
        self.client.post(
            self.get_user_promo_activate_url(self.promo3_id),
            format='json',
        )

        response = self.client.get(
            self.user_promo_history_url,
            {'limit': 0},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, [])
        self.assertEqual(response.headers['X-Total-Count'], '4')
