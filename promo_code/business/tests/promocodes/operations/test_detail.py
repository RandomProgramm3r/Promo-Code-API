import django.urls
import rest_framework.status
import rest_framework.test

import business.tests.promocodes.base


class TestPromoDetail(business.tests.promocodes.base.BasePromoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        client = rest_framework.test.APIClient()

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + cls.company1_token)
        promo1_data = {
            'description': 'Increased 10% cashback for new bank clients!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response1 = client.post(
            cls.promo_list_create_url,
            promo1_data,
            format='json',
        )
        cls.promo1_id = response1.data['id']

        client.credentials(HTTP_AUTHORIZATION='Bearer ' + cls.company2_token)
        promo2_data = {
            'description': 'We gift a globe when order exceeds 30000!',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 1,
            'active_until': '2025-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['only_youuuu', 'not_only_you'],
        }
        response2 = client.post(
            cls.promo_list_create_url,
            promo2_data,
            format='json',
        )
        cls.promo2_id = response2.data['id']

    def test_get_promo_company1(self):
        promo_detail_url = django.urls.reverse(
            'api-business:promo-detail',
            kwargs={'id': self.__class__.promo1_id},
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.get(promo_detail_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected = {
            'description': 'Increased 10% cashback for new bank clients!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
            'promo_id': str(self.promo1_id),
            'company_name': self.company1_data['name'],
            'like_count': 0,
            'used_count': 0,
        }
        for key, value in expected.items():
            self.assertEqual(response.data.get(key), value)

    def test_get_promo_company2(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo2_id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        response = self.client.get(promo_detail_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected = {
            'description': 'We gift a globe when order exceeds 30000!',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 1,
            'active_until': '2025-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['only_youuuu', 'not_only_you'],
            'promo_id': str(self.promo2_id),
            'company_name': self.company2_data['name'],
            'like_count': 0,
            'used_count': 0,
        }
        for key, value in expected.items():
            self.assertEqual(response.data.get(key), value)

    def test_patch_description_image_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {
            'description': '100% Cashback',
            'image_url': 'https://doesitexist.com/',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('description'), '100% Cashback')
        self.assertEqual(
            response.data.get('image_url'),
            'https://doesitexist.com/',
        )
        self.assertEqual(response.data.get('target'), {})

    def test_patch_active_from_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {'active_from': '2023-12-20'}
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('active_from'), '2023-12-20')

    def test_patch_partial_target_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {'target': {'country': 'fr', 'age_from': 28}}
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data.get('target'),
            {'country': 'fr', 'age_from': 28},
        )

    def test_patch_replace_target_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {
            'target': {'country': 'Us', 'categories': ['ios', 'footballer']},
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data.get('target'),
            {'country': 'Us', 'categories': ['ios', 'footballer']},
        )

    def test_patch_active_until_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {
            'active_until': '2050-10-08',
            'target': {'country': 'Us', 'categories': ['ios', 'footballer']},
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data.get('target'),
            {'country': 'Us', 'categories': ['ios', 'footballer']},
        )
        self.assertEqual(response.data.get('active_until'), '2050-10-08')

    def test_patch_clear_target_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {'target': {}}
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('target'), {})

    def test_patch_increase_max_count_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {'max_count': 20}
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('max_count'), 20)

    def test_patch_decrease_max_count_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {'max_count': 4}
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('max_count'), 4)

    def test_patch_edit_image_url_company2(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo2_id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        response = self.client.get(promo_detail_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIsNone(response.data.get('image_url'))
        data = {
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
        }

        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data.get('image_url'),
            'https://cdn2.thecatapi.com/images/3lo.jpg',
        )

    def test_final_get_promo_company1(self):
        promo_detail_url = self.promo_detail_url(self.__class__.promo1_id)
        data = {
            'description': '100% Cashback',
            'image_url': 'https://doesitexist.com/',
            'active_from': '2023-12-20',
            'active_until': '2050-10-08',
            'target': {},
            'max_count': 4,
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.patch(promo_detail_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.get(self.promo_list_create_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data

        promo_detail_url = django.urls.reverse(
            'api-business:promo-detail',
            kwargs={'id': self.__class__.promo1_id},
        )

        response = self.client.get(promo_detail_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected = {
            'description': '100% Cashback',
            'image_url': 'https://doesitexist.com/',
            'target': {},
            'max_count': 4,
            'active_from': '2023-12-20',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
            'promo_id': str(self.__class__.promo1_id),
            'company_name': self.company1_data['name'],
            'like_count': 0,
            'used_count': 0,
        }
        for key, value in expected.items():
            self.assertEqual(response.data.get(key), value)
