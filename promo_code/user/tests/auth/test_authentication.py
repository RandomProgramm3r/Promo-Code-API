import rest_framework.status
import rest_framework.test

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
            self.signin_url,
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
