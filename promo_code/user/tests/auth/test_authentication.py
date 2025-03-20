import django.test
import django.urls
import rest_framework.status
import rest_framework.test

import user.models


class AuthenticationTests(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        super().setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super().tearDown()

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
        self.assertIn('access', response.data)
        self.assertTrue(
            user.models.User.objects.filter(
                email='minecraft.digger@gmail.com',
            ).exists(),
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
