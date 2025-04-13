import parameterized
import rest_framework.status
import rest_framework.test

import business.models
import business.tests.promocodes.base


class TestPromoList(
    business.tests.promocodes.base.BasePromoTestCase,
):
    def _create_additional_promo(self):
        self.__class__.promo5_data = {
            'description': 'Special offer: bonus reward for loyal customers',
            'target': {'country': 'Kz'},
            'max_count': 10,
            'active_from': '2026-05-01',
            'mode': 'COMMON',
            'promo_common': 'special-10',
        }
        response_create = self.client.post(
            self.promo_create_url,
            self.__class__.promo5_data,
            format='json',
        )
        self.assertEqual(
            response_create.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    @classmethod
    def setUpTestData(cls):
        business.tests.promocodes.base.BasePromoTestCase.setUpTestData()

        cls.promo1_data = {
            'description': 'Increased cashback 10% for new bank customers!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        cls.promo2_data = {
            'description': 'Increased cashback 40% for new bank customers!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {'age_from': 15, 'country': 'fr'},
            'max_count': 100,
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_common': 'sale-40',
        }
        cls.promo3_data = {
            'description': 'Gift sleep mask when applying for a car loan',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'gb'},
            'max_count': 1,
            'active_from': '2025-01-01',
            'active_until': '2028-12-30',
            'mode': 'UNIQUE',
            'promo_unique': ['uniq1', 'uniq2', 'uniq3'],
        }
        cls.promo5_data = {
            'description': 'Special offer: bonus reward for loyal customers',
            'target': {'country': 'Kz'},
            'max_count': 10,
            'active_from': '2026-05-01',
            'mode': 'COMMON',
            'promo_common': 'special-10',
        }
        cls.created_promos = []

        for promo_data in [cls.promo1_data, cls.promo2_data, cls.promo3_data]:
            promo = business.models.Promo.objects.create(
                company=cls.company1,
                description=promo_data['description'],
                image_url=promo_data.get('image_url'),
                target=promo_data['target'],
                max_count=promo_data['max_count'],
                active_from=promo_data.get('active_from'),
                active_until=promo_data.get('active_until'),
                mode=promo_data['mode'],
            )
            if promo.mode == 'COMMON':
                promo.promo_common = promo_data.get('promo_common')
                promo.save()
            else:
                promo_codes = [
                    business.models.PromoCode(promo=promo, code=code)
                    for code in promo_data.get('promo_unique', [])
                ]
                business.models.PromoCode.objects.bulk_create(promo_codes)

            cls.created_promos.append(promo)

    def setUp(self):
        self.client = rest_framework.test.APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )

    def test_get_all_promos(self):
        response = self.client.get(self.promo_list_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(data[2]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(response.headers.get('X-Total-Count'), '3')

    def test_get_promos_with_pagination_offset_1(self):
        response = self.client.get(self.promo_list_url, {'offset': 1})
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(response.headers.get('X-Total-Count'), '3')

    def test_get_promos_with_pagination_offset_1_limit_1(self):
        response = self.client.get(
            self.promo_list_url,
            {'offset': 1, 'limit': 1},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(response.get('X-Total-Count'), '3')

    def test_get_promos_with_pagination_offset_100(self):
        response = self.client.get(self.promo_list_url, {'offset': 100})
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data
        self.assertEqual(len(data), 0)
        self.assertEqual(response.get('X-Total-Count'), '3')

    def test_get_promos_filter_country_gb(self):
        response = self.client.get(self.promo_list_url, {'country': 'gb'})
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(response.get('X-Total-Count'), '2')

    def test_get_promos_filter_country_gb_sort_active_until(self):
        response = self.client.get(
            self.promo_list_url,
            {'country': 'gb', 'sort_by': 'active_until'},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(response.get('X-Total-Count'), '2')

    def test_get_promos_filter_country_gb_fr_sort_active_from_limit_10(self):
        response = self.client.get(
            self.promo_list_url,
            {'country': 'gb,FR', 'sort_by': 'active_from', 'limit': 10},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(data[2]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(response.get('X-Total-Count'), '3')

    def test_get_promos_filter_country_gb_fr_sort_active_from_limit_2_offset_2(
        self,
    ):
        response = self.client.get(
            self.promo_list_url,
            {
                'country': 'gb,FR',
                'sort_by': 'active_from',
                'limit': 2,
                'offset': 2,
            },
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(response.get('X-Total-Count'), '3')

    def test_get_promos_filter_country_gb_fr_us_sort_active_from_limit_2(self):
        response = self.client.get(
            self.promo_list_url,
            {'country': 'gb,FR,us', 'sort_by': 'active_from', 'limit': 2},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(response.get('X-Total-Count'), '3')

    def test_get_promos_limit_zero(self):
        response = self.client.get(self.promo_list_url, {'limit': 0})
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data
        self.assertEqual(len(data), 0)

    def test_create_and_get_promos(self):
        self._create_additional_promo()

        response_list = self.client.get(
            self.promo_list_url,
            {'country': 'gb,FR,Kz', 'sort_by': 'active_from', 'limit': 10},
        )
        self.assertEqual(
            response_list.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response_list.data

        self.assertEqual(len(data), 4)
        self.assertEqual(response_list.get('X-Total-Count'), '4')

    def test_get_promos_filter_gb_kz_fr(self):
        self._create_additional_promo()
        response = self.client.get(
            self.promo_list_url,
            {'country': 'gb,Kz,FR', 'sort_by': 'active_from', 'limit': 10},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 4)
        self.assertEqual(response.get('X-Total-Count'), '4')

    def test_get_promos_filter_kz_sort_active_until(self):
        self._create_additional_promo()
        response = self.client.get(
            self.promo_list_url,
            {'country': 'Kz', 'sort_by': 'active_until', 'limit': 10},
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), 2)
        self.assertEqual(response.get('X-Total-Count'), '2')

    @parameterized.parameterized.expand(
        [
            ('comma_separated', {'country': 'gb,FR'}, 3),
            ('multiple_params', {'country': ['gb', 'FR']}, 3),
        ],
    )
    def test_country_parameter_formats(self, _, params, expected_count):
        full_params = {
            **params,
            'sort_by': 'active_from',
            'limit': 10,
        }

        response = self.client.get(self.promo_list_url, full_params)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        self.assertEqual(len(data), expected_count)
        self.assertEqual(data[0]['promo_id'], str(self.created_promos[1].id))
        self.assertEqual(data[1]['promo_id'], str(self.created_promos[0].id))
        self.assertEqual(data[2]['promo_id'], str(self.created_promos[2].id))
        self.assertEqual(response['X-Total-Count'], str(expected_count))
