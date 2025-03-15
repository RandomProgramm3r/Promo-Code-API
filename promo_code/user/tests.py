import django.test
import django.urls
import parameterized
import rest_framework.status
import rest_framework.test
import rest_framework_simplejwt.token_blacklist.models as tb_models

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


class JWTTests(rest_framework.test.APITestCase):
    def setUp(self):

        self.signin_url = django.urls.reverse('api-user:sign-in')
        self.protected_url = django.urls.reverse('api-core:protected')
        self.refresh_url = django.urls.reverse('api-user:token_refresh')
        user.models.User.objects.create_user(
            name='John',
            surname='Doe',
            email='example@example.com',
            password='SuperStrongPassword2000!',
            other={'age': 25, 'country': 'us'},
        )
        self.user_data = {
            'email': 'example@example.com',
            'password': 'SuperStrongPassword2000!',
        }

        super(JWTTests, self).setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()

        super(JWTTests, self).tearDown()

    def test_access_protected_view_with_valid_token(self):
        response = self.client.post(
            self.signin_url,
            self.user_data,
            format='json',
        )

        token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'request was permitted')

    def test_refresh_token_invalidation_after_new_login(self):

        first_login_response = self.client.post(
            self.signin_url,
            self.user_data,
            format='json',
        )
        refresh_token_v1 = first_login_response.data['refresh']

        second_login_response = self.client.post(
            self.signin_url,
            self.user_data,
            format='json',
        )
        refresh_token_v2 = second_login_response.data['refresh']

        refresh_response_v1 = self.client.post(
            self.refresh_url,
            {'refresh': refresh_token_v1},
            format='json',
        )
        self.assertEqual(
            refresh_response_v1.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(refresh_response_v1.data['code'], 'token_not_valid')
        self.assertEqual(
            str(refresh_response_v1.data['detail']),
            'Token is blacklisted',
        )

        refresh_response_v2 = self.client.post(
            self.refresh_url,
            {'refresh': refresh_token_v2},
            format='json',
        )
        self.assertEqual(
            refresh_response_v2.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('access', refresh_response_v2.data)

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + first_login_response.data['access'],
        )
        protected_response = self.client.get(self.protected_url)
        self.assertEqual(
            protected_response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_blacklist_storage(self):

        self.client.post(self.signin_url, self.user_data, format='json')

        self.client.post(self.signin_url, self.user_data, format='json')

        self.assertEqual(
            (tb_models.BlacklistedToken.objects.count()),
            1,
        )
        self.assertEqual(
            (tb_models.OutstandingToken.objects.count()),
            2,
        )

    def test_token_version_increment(self):
        response1 = self.client.post(
            self.signin_url,
            self.user_data,
            format='json',
        )
        self.assertEqual(response1.data['token_version'], 1)

        response2 = self.client.post(
            self.signin_url,
            self.user_data,
            format='json',
        )
        self.assertEqual(response2.data['token_version'], 2)

        user_ = user.models.User.objects.get(email=self.user_data['email'])
        self.assertEqual(user_.token_version, 2)
