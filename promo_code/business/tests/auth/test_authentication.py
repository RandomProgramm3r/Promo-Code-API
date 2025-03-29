import rest_framework.status
import rest_framework.test

import business.models
import business.tests.auth.base


class AuthenticationTests(business.tests.auth.base.BaseBusinessAuthTestCase):
    def test_signin_success(self):
        registration_data = {**self.valid_data, 'email': 'unique@company.com'}
        business.models.Company.objects.create_company(
            name=registration_data['name'],
            email=registration_data['email'],
            password=registration_data['password'],
        )
        self.assertTrue(
            business.models.Company.objects.filter(
                email=registration_data['email'],
            ).exists(),
        )

        response = self.client.post(
            self.signin_url,
            {
                'email': registration_data['email'],
                'password': registration_data['password'],
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertIn('access', response.data)
