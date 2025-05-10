import uuid

import parameterized
import rest_framework.status

import user.tests.user.base


class TestUserPromoDetail(user.tests.user.base.BaseUserTestCase):
    def setUp(self):
        super().setUp()
        signup_payload = {
            'name': 'Leslie',
            'surname': 'Lamport',
            'email': 'leslie@lamport.com',
            'password': 'Everyth1ngIsDistributed!',
            'other': {'age': 80, 'country': 'sg'},
        }
        response = self.client.post(
            self.user_signup_url,
            signup_payload,
            format='json',
        )
        self.user_token = response.data.get('access')

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )

        promo_kz = {
            'description': 'Live COMMON voucher for Kazakhstani users',
            'target': {'country': 'kz'},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp1 = self.client.post(
            self.promo_list_create_url,
            promo_kz,
            format='json',
        )
        self.promo_kz_id = resp1.data.get('id')

        promo_sg = {
            'description': 'Live COMMON voucher for Singapore residents',
            'target': {'country': 'sg'},
            'max_count': 1000,
            'active_from': '2023-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp2 = self.client.post(
            self.promo_list_create_url,
            promo_sg,
            format='json',
        )
        self.promo_sg_id = resp2.data.get('id')

        promo_us = {
            'description': 'Gift sleeping mask with car loan application',
            'target': {
                'age_from': 28,
                'age_until': 50,
                'country': 'us',
                'categories': ['cars'],
            },
            'max_count': 1,
            'active_from': '2025-01-01',
            'active_until': '2028-12-30',
            'mode': 'UNIQUE',
            'promo_unique': ['uniq1', 'uniq2', 'uniq3'],
        }

        resp3 = self.client.post(
            self.promo_list_create_url,
            promo_us,
            format='json',
        )
        self.promo_us_id = resp3.data.get('id')

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.user_token)

    def test_get_promo_matching_target(self):
        url = self.promo_detail_url(self.promo_sg_id)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            str(response.data.get('promo_id')),
            str(self.promo_sg_id),
        )

    def test_get_promo_non_matching_target(self):
        url = self.promo_detail_url(self.promo_kz_id)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            str(response.data.get('promo_id')),
            str(self.promo_kz_id),
        )
        self.assertEqual(
            response.data.get('description'),
            'Live COMMON voucher for Kazakhstani users',
        )

    @parameterized.parameterized.expand(
        [
            ('promo_sg_id', 'promo_common'),
            ('promo_kz_id', 'promo_common'),
            ('promo_us_id', 'promo_unique'),
        ],
    )
    def test_user_promo_detail(self, promo_attr, forbidden_field):
        promo_id = getattr(self, promo_attr)
        url = self.promo_detail_url(promo_id)
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        self.assertNotContains(
            response,
            forbidden_field,
        )

    def test_get_promo_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.jwt.token')
        url = self.promo_detail_url(self.promo_kz_id)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_promo_not_found(self):
        random_uuid = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')
        url = self.promo_detail_url(random_uuid)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_404_NOT_FOUND,
        )
