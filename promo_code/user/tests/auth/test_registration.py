import rest_framework.status
import rest_framework.test

import user.models
import user.tests.auth.base


class UserRegistrationTests(user.tests.auth.base.BaseUserAuthTestCase):
    def test_registration_success(self):
        valid_data = {
            'name': 'Emma',
            'surname': 'Thompson',
            'email': 'example@gmail.com',
            'password': 'SuperStrongPassword2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            self.signup_url,
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
