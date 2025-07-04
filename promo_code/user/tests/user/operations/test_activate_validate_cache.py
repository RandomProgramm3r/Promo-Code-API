import time

import requests
import rest_framework.status

import user.tests.user.base


class TestPromoCodeActivationValidateCache(
    user.tests.user.base.BaseUserTestCase,
):
    def setUp(self):
        super().setUp()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        promo_data = {
            'description': 'Active COMMON promo for all',
            'target': {},
            'max_count': 100,
            'active_from': '2024-01-01',
            'mode': 'COMMON',
            'promo_common': 'sale-for-all',
        }
        response = self.client.post(
            self.promo_list_create_url,
            promo_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        self.promo1_id = response.data['id']

        user4_data = {
            'name': 'Mason',
            'surname': 'Jones',
            'email': 'dontstopthemusic@gmail.com',
            'password': 'PasswordForMason123!',
            'other': {'age': 25, 'country': 'ca'},
        }
        response = self.client.post(
            self.user_signup_url,
            user4_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.user4_token = response.data['access']
        self.user4_email = user4_data['email']

        user5_data = {
            'name': 'Chloe',
            'surname': 'Taylor',
            'email': 'slowdown@antifraud.ru',
            'password': 'PasswordForChloe456!',
            'other': {'age': 32, 'country': 'au'},
        }
        response = self.client.post(
            self.user_signup_url,
            user5_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.user5_token = response.data['access']

    def test_promo_activation_and_antifraud_block_with_delay(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user4_token,
        )
        response = requests.post(
            self.antifraud_update_user_verdict_url,
            json={'user_email': self.user4_email, 'ok': True},
        )

        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        antifraud_verdict_data = {'user_email': self.user4_email, 'ok': False}

        antifraud_response = requests.post(
            self.antifraud_update_user_verdict_url,
            json=antifraud_verdict_data,
            timeout=5,
        )
        self.assertEqual(
            antifraud_response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        time.sleep(4)

        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_promo_activation_with_cached_antifraud_verdict(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user5_token,
        )

        start_time_0 = time.time()
        response = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
        )
        end_time_0 = time.time()
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        start_time_1 = time.time()
        response_1 = self.client.post(
            self.get_user_promo_activate_url(self.promo1_id),
        )
        end_time_1 = time.time()

        self.assertEqual(
            response_1.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        self.assertTrue((end_time_1 - start_time_1) < 1.0)
        self.assertTrue(end_time_0 - start_time_0 > end_time_1 - start_time_1)
