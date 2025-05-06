import parameterized
import rest_framework.status
import rest_framework.test

import business.tests.promocodes.base


class TestPromoList(
    business.tests.promocodes.base.BasePromoTestCase,
):
    def setUp(self):
        super().setUp()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )

    def test_get_promos_without_token(self):
        self.client.credentials()
        client = rest_framework.test.APIClient()
        response = client.get(self.promo_list_create_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    @parameterized.parameterized.expand(
        [
            (
                'invalid_sort_by_format',
                {'country': 'fr', 'sort_by': 'active_untilllll'},
            ),
            ('invalid_country_format_single', {'country': 'france'}),
            ('invalid_country_format_multiple', {'country': 'gb,us,france'}),
            ('invalid_country_does_not_exist', {'country': 'xx'}),
            ('invalid_country_too_short', {'country': 'F'}),
            ('invalid_country_format', {'country': 10}),
            ('invalid_country_empty_string', {'country': ''}),
            ('unexpected_parameter', {'unexpected': 'value'}),
            (
                'combined_invalid_parameters',
                {
                    'country': 'france',
                    'limit': -1,
                    'sort_by': 'non_existing_field',
                },
            ),
        ],
    )
    def test_invalid_query_string_parameters(self, _, params):
        response = self.client.get(self.promo_list_create_url, params)
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
        response = self.client.get(self.promo_list_create_url, params)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
