import django.test
import django.urls
import rest_framework.status
import rest_framework.test

import user.models


class AuthTestCase(django.test.TestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()

        super(AuthTestCase, self).setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()

        super(AuthTestCase, self).tearDown()

    def test_signup_success(self):
        url = django.urls.reverse('api-user:sign-up')
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'emmat1@example.com',
            'avatar_url': 'https://cdn2.thecatapi.com/images/3lo.jpg',
            'other': {'age': 25, 'country': 'US'},
            'password': 'HardPa$$w0rd!iamthewinner',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('token', response.data)
        self.assertTrue(
            user.models.User.objects.filter(
                email='emmat1@example.com',
            ).exists(),
        )

    def test_signup_duplicate_email(self):
        user.models.User.objects.create_user(
            email='emmat1@example.com',
            name='Emma',
            surname='Thompson',
            password='HardPa$$w0rd!iamthewinner',
            other={'age': 25, 'country': 'US'},
        )
        url = django.urls.reverse('api-user:sign-up')
        data = {
            'name': 'Liam',
            'surname': 'Wilson',
            'email': 'emmat1@example.com',
            'password': 'HardPa$$w0rd!iamthewinner',
            'other': {'age': 30, 'country': 'GB'},
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_409_CONFLICT,
        )
        self.assertEqual(
            response.data['message'],
            'This email address is already registered.',
        )
        self.assertEqual(user.models.User.objects.count(), 1)

    def test_signup_invalid_data(self):
        url = django.urls.reverse('api-user:sign-up')
        data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'invalid-email',
            'password': 'short',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(response.data['message'], 'Error in request data.')

    def test_signin_success(self):
        user.models.User.objects.create_user(
            email='emmat1@example.com',
            name='Emma',
            surname='Thompson',
            password='HardPa$$w0rd!iamthewinner',
            other={'age': 23, 'country': 'US'},
        )
        url = django.urls.reverse('api-user:sign-in')
        data = {
            'email': 'emmat1@example.com',
            'password': 'HardPa$$w0rd!iamthewinner',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('token', response.data)

    def test_signin_invalid_credentials(self):
        user.models.User.objects.create_user(
            email='emmat1@example.com',
            name='Emma',
            surname='Thompson',
            password='HardPa$$w0rd!iamthewinner',
            other={'age': 23, 'country': 'ru'},
        )

        url = django.urls.reverse('api-user:sign-in')
        data = {'email': 'emmat1@example.com', 'password': 'WrongPass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            response.data['message'],
            'Invalid email or password.',
        )
