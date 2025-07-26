import uuid

import django.test
import rest_framework.status
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.tokens

import business.models
import user.authentication
import user.models
import user.tests.auth.base


class UserAuthenticationTests(user.tests.auth.base.BaseUserAuthTestCase):
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
            self.user_signin_url,
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )


class CustomJWTAuthenticationTest(django.test.TestCase):
    def setUp(self):
        self.factory = django.test.RequestFactory()
        self.authenticator = user.authentication.CustomJWTAuthentication()
        self.user = user.models.User.objects.create(
            name='testuser_uuid',
            token_version=1,
        )
        self.company = business.models.Company.objects.create(
            name='testcompany_uuid',
            token_version=1,
        )

    def _get_token_with_payload(self, payload):
        token = rest_framework_simplejwt.tokens.AccessToken()
        token.payload.update(payload)
        return str(token)

    def test_authenticate_invalid_user_type(self):
        payload = {
            'user_type': 'admin',
            'user_id': str(self.user.id),
            'token_version': self.user.token_version,
        }
        token = self._get_token_with_payload(payload)
        request = self.factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        with self.assertRaisesMessage(
            rest_framework_simplejwt.exceptions.AuthenticationFailed,
            'Invalid user type',
        ):
            self.authenticator.authenticate(request)

    def test_authenticate_missing_id_in_token(self):
        payload = {
            'user_type': 'user',
            'token_version': self.user.token_version,
        }
        token = self._get_token_with_payload(payload)
        request = self.factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        with self.assertRaisesMessage(
            rest_framework_simplejwt.exceptions.AuthenticationFailed,
            'Missing user_id in token',
        ):
            self.authenticator.authenticate(request)

    def test_authenticate_mismatched_token_version(self):
        payload = {
            'user_type': 'user',
            'user_id': str(self.user.id),
            'token_version': 1,
        }
        token = self._get_token_with_payload(payload)
        self.user.token_version = 2
        self.user.save()
        request = self.factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        with self.assertRaisesMessage(
            rest_framework_simplejwt.exceptions.AuthenticationFailed,
            'Token invalid',
        ):
            self.authenticator.authenticate(request)

    def test_authenticate_user_or_company_not_found(self):
        non_existent_uuid = str(uuid.uuid4())
        payload = {
            'user_type': 'user',
            'user_id': non_existent_uuid,
            'token_version': 1,
        }
        token = self._get_token_with_payload(payload)
        request = self.factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        with self.assertRaisesMessage(
            rest_framework_simplejwt.exceptions.AuthenticationFailed,
            'User or Company not found',
        ):
            self.authenticator.authenticate(request)

    def test_authenticate_raw_token_none(self):
        request = self.factory.get('/api/test/')
        request.META['HTTP_AUTHORIZATION'] = 'Token abcdefg'
        result = self.authenticator.authenticate(request)
        self.assertIsNone(result)
