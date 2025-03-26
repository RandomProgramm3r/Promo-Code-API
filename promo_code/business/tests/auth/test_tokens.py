import business.models
import business.tests.auth.base
import rest_framework.status
import rest_framework.test


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
            self.signin_url,
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
            self.signup_url,
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
            self.signin_url,
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
