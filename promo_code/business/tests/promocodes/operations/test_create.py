import business.tests.promocodes.base
import rest_framework.status


class TestSuccessfulPromoCreation(
    business.tests.promocodes.base.BasePromoCreateTestCase,
):
    def test_successful_promo_creation_1(self):
        payload = {
            'description': 'Increased cashback 10% for new bank clients!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_2(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'image_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'target': {'age_from': 15, 'country': 'fr'},
            'max_count': 100,
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_common': 'sale-40',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_3(self):
        payload = {
            'description': 'Gift sleeping mask with car loan application',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 1,
            'active_from': '2025-01-01',
            'active_until': '2028-12-30',
            'mode': 'UNIQUE',
            'promo_unique': ['uniq1', 'uniq2', 'uniq3'],
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_4(self):
        payload = {
            'description': 'We gift a globe when ordering for 30000!',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 1,
            'active_until': '2025-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['only_youuuu', 'not_only_you'],
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_5(self):
        payload = {
            'description': 'Increased cashback 10% for new bank clients!',
            'image_url': 'http://cdn2.thecatapi.com/',
            'target': {},
            'max_count': 10,
            'active_from': '1950-01-01',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_6_country_lower(self):
        payload = {
            'description': 'Increased cashback 10% for new bank clients!',
            'image_url': 'http://cdn2.thecatapi.com/',
            'target': {'country': 'Us'},
            'max_count': 10,
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_6_country_upper(self):
        payload = {
            'description': 'Increased cashback 10% for new bank clients!',
            'image_url': 'http://cdn2.thecatapi.com/',
            'target': {'country': 'US'},
            'max_count': 10,
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )

    def test_successful_promo_creation_7(self):
        payload = {
            'description': 'Increased cashback 10% for new bank clients!',
            'image_url': 'http://cdn2.thecatapi.com/',
            'target': {'age_from': 100, 'age_until': 100},
            'max_count': 10,
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self.token,
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
