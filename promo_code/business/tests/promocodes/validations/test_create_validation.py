import parameterized
import rest_framework.status

import business.tests.promocodes.base


class TestPromoCreate(
    business.tests.promocodes.base.BasePromoTestCase,
):
    def setUp(self):
        super().setUp()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )

    def test_create_promo_with_old_token(self):
        self.client.credentials()
        registration_data = {
            'name': 'Someone',
            'email': 'mail@mail.com',
            'password': 'SuperStrongPassword2000!',
        }
        reg_response = self.client.post(
            self.signup_url,
            registration_data,
            format='json',
        )
        old_token = reg_response.data.get('token')
        self.client.post(
            self.signin_url,
            {
                'email': registration_data['email'],
                'password': registration_data['password'],
            },
            format='json',
        )
        payload = {
            'description': 'Test promo code',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + str(old_token),
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    @parameterized.parameterized.expand(
        [
            (
                'missing_description',
                {
                    # 'description' is missing
                    'target': {},
                    'max_count': 10,
                    'active_from': '2025-01-10',
                    'mode': 'COMMON',
                    'promo_common': 'sale-10',
                },
            ),
            (
                'missing_target',
                {
                    'description': (
                        'Increased cashback 40% for new bank clients!',
                    ),
                    'max_count': 100,
                    'active_from': '2028-12-20',
                    'mode': 'COMMON',
                    'promo_common': 'sale-40',
                    # 'target' is missing
                },
            ),
            (
                'missing_promo_common',
                {
                    'description': (
                        'Increased cashback 40% for new bank clients!',
                    ),
                    'max_count': 100,
                    'target': {},
                    'active_from': '2028-12-20',
                    'mode': 'COMMON',
                    # 'promo_common' is missing
                },
            ),
        ],
    )
    def test_missing_fields(self, name, payload):
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_mode(self):
        payload = {
            'description': 'Gift sleeping mask with car loan application',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 1,
            'active_from': '2025-01-01',
            'active_until': '2028-12-30',
            'mode': 'EMINEM',  # invalid mode
            'promo_unique': ['uniq1', 'uniq2', 'uniq3'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_max_count_for_unique_mode(self):
        payload = {
            'description': 'Gift sleeping mask with car loan application',
            'target': {'age_from': 28, 'age_until': 50, 'country': 'us'},
            'max_count': 3,  # invalid for UNIQUE mode
            'active_from': '2025-01-01',
            'active_until': '2028-12-30',
            'mode': 'UNIQUE',
            'promo_unique': ['uniq1', 'uniq2', 'uniq3'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_short_description(self):
        payload = {
            'description': 'small',  # too short description
            'target': {'age_from': 28, 'age_until': 50, 'country': 'US'},
            'max_count': 1,
            'active_until': '2025-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['only_youuuu', 'not_only_you'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand([('Vietnam'), ('XX')])
    def test_invalid_country(self, invalid_country):
        payload = {
            'description': 'A valid description with sufficient length',
            'target': {
                'age_from': 28,
                'age_until': 50,
                'country': invalid_country,
            },
            'max_count': 1,
            'active_until': '2025-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['only_youuuu', 'not_only_you'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_nonexistent_country(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 100,
            'target': {'country': 'aa'},  # non-existent country
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_common': 'sale-40',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_age_range(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 100,
            'target': {
                'age_from': 50,
                'age_until': 49,  # invalid: from > until
            },
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_common': 'sale-40',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_common_with_promo_unique_provided(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 100,
            'target': {},
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_unique': ['sale-40'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_unique_with_promo_common_provided(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 1,
            'target': {},
            'active_from': '2028-12-20',
            'mode': 'UNIQUE',
            'promo_common': 'sale-40',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_both_promo_common_and_promo_unique_provided(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 1,
            'target': {},
            'active_from': '2028-12-20',
            'mode': 'UNIQUE',
            'promo_common': 'sale-40',
            'promo_unique': ['opa'],
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_too_short_promo_common(self):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': 100,
            'target': {},
            'active_from': '2028-12-20',
            'mode': 'COMMON',
            'promo_common': 'str',  # too short
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            (
                'invalid_type_for_promo_unique',
                {
                    'description': (
                        'Increased cashback 40% for new bank clients!'
                    ),
                    'max_count': 1,
                    'target': {},
                    'active_from': '2028-12-20',
                    'mode': 'UNIQUE',
                    'promo_unique': 123,  # invalid type, should be a list
                },
            ),
            (
                'invalid_type_for_max_count',
                {
                    'description': (
                        'Increased cashback 40% for new bank clients!'
                    ),
                    'max_count': 'fifty',  # invalid type
                    'target': {},
                    'active_from': '2028-12-20',
                    'mode': 'COMMON',
                    'promo_common': 'sale-40',
                },
            ),
            (
                'invalid_type_for_target',
                {
                    'description': (
                        'Increased cashback 40% for new bank clients!'
                    ),
                    'max_count': 1,
                    'target': 123,  # invalid type
                    'active_from': '2028-12-20',
                    'mode': 'UNIQUE',
                    'promo_unique': ['opa'],
                },
            ),
        ],
    )
    def test_invalid_type_payloads(self, name, payload):
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            (-1),
            (100000001),
            (1000000000001),
        ],
    )
    def test_invalid_max_count(self, max_count):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'max_count': max_count,
            'target': {},
            'mode': 'COMMON',
            'promo_common': 'something-here',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('itsnotalink'),
            ('hello@com'),
            (''),
            ('https://'),
            (f'https://cdn2.thecatapi.com/images/3lo{"1" * 350}.jpg'),
        ],
    )
    def test_invalid_image_url(self, url):
        payload = {
            'description': 'Increased cashback 40% for new bank clients!',
            'image_url': url,
            'max_count': 1000,
            'target': {},
            'mode': 'COMMON',
            'promo_common': 'something-here',
        }
        response = self.client.post(
            self.promo_list_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
