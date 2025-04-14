import parameterized
import rest_framework.status

import business.tests.promocodes.base


class TestPromoDetail(business.tests.promocodes.base.BasePromoTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.common_payload = {
            'description': 'Complimentary Auto Giveaway',
            'target': {},
            'max_count': 10,
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        cls.unique_payload = {
            'description': 'Complimentary Pudge Skin on Registration!',
            'target': {},
            'max_count': 1,
            'mode': 'UNIQUE',
            'active_from': '2030-08-08',
            'promo_unique': ['dota-arena', 'coda-core', 'warcraft3'],
        }

    def create_promo(self, token, payload):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        return response.data['id']

    def test_create_promo_company1(self):
        promo_id = self.create_promo(self.company1_token, self.common_payload)
        self.assertTrue(promo_id)

    def test_create_promo_company2(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.assertTrue(promo_id)

    def test_old_token_invalid_after_reauthentication(self):
        promo_id = self.create_promo(self.company1_token, self.common_payload)
        old_token = self.company1_token

        self.client.credentials()
        signin_payload = {
            'email': self.company1_data['email'],
            'password': self.company1_data['password'],
        }
        response = self.client.post(
            self.signin_url,
            signin_payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.company1_token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + old_token)
        url = self.promo_detail_url(promo_id)
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_edit_nonexistent_promo(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        non_existent_uuid = '550e8400-e29b-41d4-a716-446655440000'
        url = self.promo_detail_url(non_existent_uuid)
        patch_payload = {'description': '100% Cashback'}
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_404_NOT_FOUND,
        )

    def test_edit_foreign_promo(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        url = self.promo_detail_url(promo_id)
        patch_payload = {'description': '100% Cashback'}
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

    def test_edit_promo_without_authentication(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        url = self.promo_detail_url(promo_id)
        patch_payload = {'description': '100% Cashback'}
        self.client.credentials()
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_edit_invalid_short_description(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.promo_detail_url(promo_id)
        patch_payload = {'description': 'qqall'}
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            (
                'non_string',
                {'image_url': False},
            ),
            (
                'incomplete_url',
                {'image_url': 'https://'},
            ),
            (
                'malformed_url',
                {'image_url': 'notalink'},
            ),
        ],
    )
    def test_edit_invalid_image_urls(self, _, patch_payload):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.promo_detail_url(promo_id)
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            (
                'age_range_invalid',
                {
                    'description': 'Bonus 10000%!',
                    'target': {'age_from': 19, 'age_until': 17},
                },
            ),
            (
                'incomplete_target',
                {'description': 'Bonus 10000%!', 'target': {'country': 'USA'}},
            ),
            (
                'empty_category',
                {
                    'description': 'Bonus 10000%!',
                    'target': {'categories': ['']},
                },
            ),
        ],
    )
    def test_edit_invalid_target(self, _, patch_payload):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.promo_detail_url(promo_id)
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            (
                'unique_max_count',
                'company2_token',
                'unique_payload',
                {'max_count': 10},
            ),
            (
                'negative_max_count',
                'company1_token',
                'common_payload',
                {'max_count': -10},
            ),
            (
                'non_integer_max_count',
                'company1_token',
                'common_payload',
                {'max_count': 'invalid'},
            ),
            (
                'zero_max_count',
                'company2_token',
                'unique_payload',
                {'max_count': 0},
            ),
            (
                'max_count_is_none',
                'company1_token',
                'common_payload',
                {'max_count': None},
            ),
            (
                'exceeding_max_count',
                'company1_token',
                'common_payload',
                {'max_count': 100_000_001},
            ),
        ],
    )
    def test_edit_invalid_max_count(
        self,
        _,
        token_attr,
        payload_attr,
        patch_payload,
    ):
        token = getattr(self, token_attr)
        create_payload = getattr(self, payload_attr)

        promo_id = self.create_promo(token, create_payload)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = self.promo_detail_url(promo_id)

        response = self.client.patch(url, patch_payload, format='json')

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_edit_invalid_active_from(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.promo_detail_url(promo_id)
        patch_payload = {'active_from': '2024-12-28 12:00:00'}
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_get_promo_verify_fields_unchanged(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.promo_detail_url(promo_id)
        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected_data = self.unique_payload.copy()
        for key, expected in expected_data.items():
            self.assertEqual(response.data.get(key), expected)
