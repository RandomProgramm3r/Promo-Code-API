import django.test
import django.urls
import parameterized
import rest_framework.status
import rest_framework.test

import user.models


class AuthTestCase(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        super(AuthTestCase, self).setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super(AuthTestCase, self).tearDown()

    def test_valid_registration_and_email_duplication(self):
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

    def test_weak_password_common_phrase(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'whereismymoney777',
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

    def test_weak_password_missing_special_char(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'fioejifojfieoAAAA9299',
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

    def test_weak_password_too_short(self):
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'dota.for.fan@gmail.com',
            'password': 'Aa7$b!',
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


class AuthFlowTestCase(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        super(AuthFlowTestCase, self).setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super(AuthFlowTestCase, self).tearDown()

    def test_valid_registration(self):
        data = {
            'name': 'Steve',
            'surname': 'Jobs',
            'email': 'minecraft.digger@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'gb'},
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-up'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('token', response.data)
        self.assertTrue(
            user.models.User.objects.filter(
                email='minecraft.digger@gmail.com',
            ).exists(),
        )

    def test_signin_missing_fields(self):
        response = self.client.post(
            django.urls.reverse('api-user:sign-in'),
            {},  # Empty data
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

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

    def test_signin_success(self):
        user.models.User.objects.create_user(
            email='minecraft.digger@gmail.com',
            name='Steve',
            surname='Jobs',
            password='SuperStrongPassword2000!',
            other={'age': 23, 'country': 'gb'},
        )

        data = {
            'email': 'minecraft.digger@gmail.com',
            'password': 'SuperStrongPassword2000!',
        }
        response = self.client.post(
            django.urls.reverse('api-user:sign-in'),
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
