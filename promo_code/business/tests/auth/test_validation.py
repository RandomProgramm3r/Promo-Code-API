import parameterized
import rest_framework.status

import business.models
import business.tests.auth.base


class InvalidCompanyRegistrationTestCase(
    business.tests.auth.base.BaseBusinessAuthTestCase,
):
    def test_duplicate_email_registration(self):
        business.models.Company.objects.create_company(
            name=self.valid_data['name'],
            email=self.valid_data['email'],
            password=self.valid_data['password'],
        )
        self.assertTrue(
            business.models.Company.objects.filter(
                email=self.valid_data['email'],
            ).exists(),
        )

        response = self.client.post(
            self.company_signup_url,
            self.valid_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_409_CONFLICT,
        )

    @parameterized.parameterized.expand(
        [
            ('short_password_1', 'easypwd'),
            ('short_password_2', 'Ar1@!$'),
            ('no_digits', 'PasswordWithoutDigits'),
            ('no_special_chars', 'PasswordWithoutSpecial1'),
            ('common_phrase', 'whereismymoney777'),
            ('missing_uppercase', 'lowercase123$'),
            ('missing_lowercase', 'UPPERCASE123$'),
            ('non_ascii', 'Päss123$!AAd'),
            ('emoji', '😎werY!!*Dj3sd'),
        ],
    )
    def test_invalid_password_cases(self, _, invalid_password):
        test_data = {**self.valid_data, 'password': invalid_password}
        response = self.client.post(
            self.company_signup_url,
            test_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
            f'Failed for password: {invalid_password}',
        )

    @parameterized.parameterized.expand(
        [
            ('domain_missing_dot', 'a@b'),
            ('domain_missing_dot', 'test@dom'),
            ('missing_local_part', '@domain.com'),
            ('missing_at_symbol', 'missing.at.sign'),
            ('multiple_at_symbols', 'double@@at.com'),
        ],
    )
    def test_invalid_email_cases(self, _, invalid_email):
        test_data = {**self.valid_data, 'email': invalid_email}
        response = self.client.post(
            self.company_signup_url,
            test_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
            f'Failed for email: {invalid_email}',
        )

    def test_short_company_name(self):
        test_data = {**self.valid_data, 'name': 'A'}
        response = self.client.post(
            self.company_signup_url,
            test_data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_create_company_missing_email_fiels(self):
        with self.assertRaisesMessage(
            ValueError,
            'The Email must be set',
        ):
            business.models.Company.objects.create_company(
                name=self.valid_data['name'],
                password=self.valid_data['password'],
                email=None,
            )


class InvalidCompanyAuthenticationTestCase(
    business.tests.auth.base.BaseBusinessAuthTestCase,
):
    @parameterized.parameterized.expand(
        [
            ('missing_password', {'email': 'valid@example.com'}, 'password'),
            ('missing_email', {'password': 'any'}, 'email'),
            ('empty_data', {}, ['email', 'password']),
        ],
    )
    def test_missing_required_fields(self, _, data, expected_fields):
        response = self.client.post(
            self.company_signin_url,
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_signin_invalid_password(self):
        business.models.Company.objects.create_company(
            email=self.valid_data['email'],
            name=self.valid_data['name'],
            password=self.valid_data['password'],
        )

        data = {
            'email': self.valid_data['email'],
            'password': 'SuperInvalidPassword2000!',
        }
        response = self.client.post(
            self.company_signin_url,
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_signin_invalid_email(self):
        business.models.Company.objects.create_company(
            email=self.valid_data['email'],
            name=self.valid_data['name'],
            password=self.valid_data['password'],
        )

        data = {
            'email': 'example11@example.com',
            'password': self.valid_data['password'],
        }
        response = self.client.post(
            self.company_signin_url,
            data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )
