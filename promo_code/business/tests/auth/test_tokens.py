import rest_framework.status
import rest_framework.test
import rest_framework_simplejwt.tokens

import business.models
import business.tests.auth.base
import user.models


class JWTTests(business.tests.auth.base.BaseBusinessAuthTestCase):
    def setUp(self):
        super().setUp()
        business.models.Company.objects.create_company(
            name='Digital Marketing Solutions Inc.',
            email='testcompany@example.com',
            password='SuperStrongPassword2000!',
        )

        self.user_data = {
            'email': 'testcompany@example.com',
            'password': 'SuperStrongPassword2000!',
        }

    def test_access_protected_view_with_valid_token(self):
        response = self.client.post(
            self.company_signin_url,
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
            'name': 'Digital Marketing Solutions Inc.',
        }
        response = self.client.post(
            self.company_signup_url,
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
            self.company_signin_url,
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


class TestCompanyTokenRefresh(
    business.tests.auth.base.BaseBusinessAuthTestCase,
):
    def setUp(self):
        super().setUp()

        self.company = business.models.Company.objects.create_company(
            name='Digital Marketing Solutions Inc.',
            email='testcompany@example.com',
            password='SuperStrongPassword2000!',
            token_version=1,
        )

        self.company_data = {
            'email': 'testcompany@example.com',
            'password': 'SuperStrongPassword2000!',
        }

        self.company_refresh = rest_framework_simplejwt.tokens.RefreshToken()
        self.company_refresh.payload.update(
            {
                'user_type': 'company',
                'company_id': str(self.company.id),
                'token_version': self.company.token_version,
            },
        )

        self.user = user.models.User.objects.create_user(
            email='minecraft.digger@gmail.com',
            name='Steve',
            surname='Jobs',
            password='SuperStrongPassword2000!',
            other={'age': 23, 'country': 'gb'},
        )
        self.user_refresh = (
            rest_framework_simplejwt.tokens.RefreshToken.for_user(self.user)
        )
        self.user_refresh.payload['user_type'] = 'user'

    def test_successful_company_token_refresh(self):
        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(self.company_refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        self.assertNotEqual(self.company_refresh, response.data['refresh'])

    def test_reject_user_tokens(self):
        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(self.user_refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertIn(
            'This refresh endpoint is for company tokens only',
            str(response.content),
        )

    def test_token_version_mismatch(self):
        self.company.token_version = 2
        self.company.save()

        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(self.company_refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertIn('Token is blacklisted', str(response.content))

    def test_missing_company_id(self):
        invalid_refresh = rest_framework_simplejwt.tokens.RefreshToken()
        invalid_refresh.payload.update(
            {'user_type': 'company', 'token_version': 1},
        )

        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(invalid_refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertIn(
            'Invalid or missing company_id in token',
            str(response.content.decode()),
        )

    def test_company_not_found(self):
        invalid_refresh = rest_framework_simplejwt.tokens.RefreshToken()
        invalid_refresh.payload.update(
            {
                'user_type': 'company',
                'company_id': 'da3ad08d-9b86-41ff-ad70-a30a64d3d170',
                'token_version': 1,
            },
        )

        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(invalid_refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertIn('Company not found', str(response.content))

    def test_refresh_token_invalidation_after_new_login(self):
        first_login_response = self.client.post(
            self.company_signin_url,
            self.company_data,
            format='json',
        )
        refresh_token_v1 = first_login_response.data['refresh']

        second_login_response = self.client.post(
            self.company_signin_url,
            self.company_data,
            format='json',
        )
        refresh_token_v2 = second_login_response.data['refresh']

        refresh_response_v1 = self.client.post(
            self.company_refresh_url,
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
            self.company_refresh_url,
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

    def test_default_user_type_handling(self):
        refresh = rest_framework_simplejwt.tokens.RefreshToken.for_user(
            self.user,
        )
        response = self.client.post(
            self.company_refresh_url,
            {'refresh': str(refresh)},
        )

        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertIn(
            'This refresh endpoint is for company tokens only',
            str(response.content),
        )
