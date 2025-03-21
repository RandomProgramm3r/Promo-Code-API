import django.test
import django.urls
import parameterized
import rest_framework.status
import rest_framework.test

import user.models


class RegistrationTestCase(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        super().setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super().tearDown()

    def test_email_duplication(self):
        valid_data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'emmat1@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            valid_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        duplicate_data = {
            'name': 'Lui',
            'surname': 'Jomalone',
            'email': 'emmat1@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 14, 'country': 'fr'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            duplicate_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_409_CONFLICT,
        )

    def test_invalid_email_format(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.fan',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('common_phrase', 'whereismymoney777'),
            ('missing_special_char', 'fioejifojfieoAAAA9299'),
            ('too_short', 'Aa7$b!'),
            ('missing_uppercase', 'lowercase123$'),
            ('missing_lowercase', 'UPPERCASE123$'),
            ('missing_digits', 'PasswordSpecial$'),
            ('non_ascii', 'Päss123$!AAd'),
            ('emoji', '😎werY!!*Dj3sd'),
        ],
    )
    def test_weak_password_cases(self, case_name, password):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': f'test.user+{case_name}@example.com',
            'password': password,
            'other': {'age': 23, 'country': 'us'},
        }

        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
            f'Failed for case: {case_name}. Response: {response.data}',
        )

    def generate_test_cases():
        invalid_urls = [
            'itsnotalink',
            'itsnotalinkjpeg',
            'https://',
            'grpc://',
            '',
        ]
        return [
            (f'url_{i}', url, f'{i}dota.for.fan@gmail.com')
            for i, url in enumerate(invalid_urls)
        ]

    @parameterized.parameterized.expand(generate_test_cases())
    def test_invalid_avatar_urls(self, name, url, email):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': email,
            'password': 'SuperStrongPassword2000!',
            'avatar_url': url,
            'other': {'age': 23, 'country': 'us'},
        }

        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
            msg=f'Failed for URL: {url}',
        )

    def test_missing_country_field(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_age_type(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': '23aaaaaa', 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_missing_age_field(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_negative_age_value(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': -20, 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('empty_domain', '@'),
            ('no_at_symbol', 'dota'),
            ('missing_username', '@gmail.com'),
            ('missing_domain_part', 'gmail.com'),
        ],
    )
    def test_invalid_email_formats(self, name, email):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': email,
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }

        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
            msg=f'Failed for email: {email}',
        )

    def test_empty_name_field(self):
        data = {
            'name': '',
            'surname': 'Thompson',
            'email': 'gogogonow@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_surname_field(self):

        data = {
            'name': 'Emma',
            'surname': '',
            'email': 'gogogonow@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )


class AuthenticationTestCase(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        self.signin_url = django.urls.reverse('api-user:sign-in')
        super().setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super().tearDown()

    @parameterized.parameterized.expand(
        [
            ('missing_password', {'email': 'valid@example.com'}, 'password'),
            ('missing_email', {'password': 'any'}, 'email'),
            ('empty_data', {}, ['email', 'password']),
        ],
    )
    def test_missing_required_fields(self, case_name, data, expected_fields):
        response = self.client.post(self.signin_url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

        if isinstance(expected_fields, list):
            for field in expected_fields:
                self.assertIn(field, response.data)
        else:
            self.assertIn(expected_fields, response.data)

    def test_signin_invalid_password(self):
        user.models.User.objects.create_user(
            email='minecraft.digger@gmail.com',
            name='Steve',
            surname='Jobs',
            password='SuperStrongPassword2000!',
            other={'age': 23, 'country': 'gb'},
        )

        data = {
            'email': 'minecraft.digger@gmail.com',
            'password': 'SuperInvalidPassword2000!',
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-in'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
