import parameterized
import rest_framework.status
import rest_framework.test

import user.tests.user.base


class TestUserPromoFeed(
    user.tests.user.base.BaseUserTestCase,
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user1_payload = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator1@apple.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user1_payload,
            format='json',
        )

        cls.user1_token = resp.data['access']
        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.user1_token,
        )

    def setUp(self):
        super().setUp()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )

    def test_get_promos_without_token(self):
        self.client.credentials()
        client = rest_framework.test.APIClient()
        response = client.get(self.user_feed_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    @parameterized.parameterized.expand(
        [
            (
                'invalid_category_too_short',
                {'category': 'A'},
            ),
            (
                'invalid_category_too_long',
                {'category': 'averylongcategorynamethatexceedstwenty'},
            ),
            (
                'invalid_category_empty_string',
                {'category': ''},
            ),
            (
                'unexpected_parameter',
                {'unexpected': 'value'},
            ),
            (
                'combined_invalid_parameters',
                {
                    'category': 'A',
                    'limit': -1,
                    'sort_by': 'non_existing_field',
                },
            ),
            (
                'non-boolean_active_format',
                {'active': 'abc'},
            ),
            (
                'non-boolean_active_format_2',
                {'active': 123},
            ),
            (
                'non-boolean_active_format_3',
                {'active': 1.5},
            ),
        ],
    )
    def test_invalid_query_string_parameters(self, _, params):
        response = self.client.get(self.user_feed_url, params)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('invalid_limit_format', {'limit': 'france'}),
            ('invalid_offset_format', {'offset': 'france'}),
            ('negative_offset', {'offset': -5}),
            ('negative_limit', {'limit': -5}),
            ('invalid_float_limit', {'limit': 5.5}),
            ('invalid_float_offset', {'offset': 3.5}),
            ('empty_string_limit', {'limit': ''}),
            ('empty_string_offset', {'offset': ''}),
        ],
    )
    def test_invalid_numeric_parameters(self, _, params):
        response = self.client.get(self.user_feed_url, params)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
