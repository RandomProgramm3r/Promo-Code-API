import rest_framework.status
import rest_framework_simplejwt.token_blacklist.models as tb_models

import user.models
import user.tests.auth.base


class JWTTests(user.tests.auth.base.BaseUserAuthTestCase):
    def setUp(self):
        super().setUp()
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

    def test_access_protected_view_with_valid_token(self):
        response = self.client.post(
            self.user_signin_url,
            self.user_data,
            format='json',
        )

        token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        response = self.client.get(self.protected_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['status'], 'request was permitted')

    def test_registration_token_invalid_after_login(self):
        data = {
            'email': 'test@example.com',
            'password': 'StrongPass123!cd',
            'name': 'John',
            'surname': 'Doe',
            'other': {'age': 22, 'country': 'us'},
        }
        response = self.client.post(
            self.user_signup_url,
            data,
            format='json',
        )
        reg_access_token = response.data['access']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {reg_access_token}',
        )
        response = self.client.get(self.protected_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        login_data = {'email': data['email'], 'password': data['password']}
        response = self.client.post(
            self.user_signin_url,
            login_data,
            format='json',
        )
        login_access_token = response.data['access']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {reg_access_token}',
        )
        response = self.client.get(self.protected_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {login_access_token}',
        )
        response = self.client.get(self.protected_url)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

    def test_refresh_token_invalidation_after_new_login(self):
        first_login_response = self.client.post(
            self.user_signin_url,
            self.user_data,
            format='json',
        )

        refresh_token_v1 = first_login_response.data['refresh']

        second_login_response = self.client.post(
            self.user_signin_url,
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
        self.client.post(self.user_signin_url, self.user_data, format='json')

        self.client.post(self.user_signin_url, self.user_data, format='json')

        self.assertEqual(
            (tb_models.BlacklistedToken.objects.count()),
            1,
        )
        self.assertEqual(
            (tb_models.OutstandingToken.objects.count()),
            2,
        )
