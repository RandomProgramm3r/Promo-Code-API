import django.urls
import rest_framework.status
import rest_framework.test

import user.models


class RegistrationTests(rest_framework.test.APITestCase):
    def setUp(self):
        self.client = rest_framework.test.APIClient()
        super().setUp()

    def tearDown(self):
        user.models.User.objects.all().delete()
        super().tearDown()

    def test_registration_success(self):
        valid_data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'example@gmail.com',
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
        self.assertTrue(
            user.models.User.objects.filter(
                email='example@gmail.com',
            ).exists(),
        )
