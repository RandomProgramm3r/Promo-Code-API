import rest_framework.status
import rest_framework.test

import business.models
import business.tests.auth.base


class TestCompanyRegistration(
    business.tests.auth.base.BaseBusinessAuthTestCase,
):
    def test_registration_success(self):
        registration_data = {**self.valid_data, 'email': 'unique@company.com'}
        response = self.client.post(
            self.signup_url,
            registration_data,
            format='json',
        )
        self.assertTrue(
            business.models.Company.objects.filter(
                email=registration_data['email'],
            ).exists(),
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
