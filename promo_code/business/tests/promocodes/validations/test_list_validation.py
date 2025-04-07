import parameterized
import rest_framework.status

import business.tests.promocodes.base


class CompanyPromoFetchTests(
    business.tests.promocodes.base.BasePromoCreateTestCase,
):

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    @parameterized.parameterized.expand(
        [
            (
                'invalid_sort_by_format',
                {'country': 'fr', 'sort_by': 'active_untilllll'},
            ),
            ('invalid_country_format_single', {'country': 'france'}),
            ('invalid_country_format_multiple', {'country': 'gb,us,france'}),
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
    def test_invalid_query_string_parameters(self, name, params):
        response = self.client.get(self.promo_list_url, params)
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
    def test_invalid_numeric_parameters(self, name, params):
        response = self.client.get(self.promo_list_url, params)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
