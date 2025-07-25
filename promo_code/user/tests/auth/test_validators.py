import django.core.exceptions
import django.test

import user.validators


class PasswordValidatorTests(django.test.TestCase):
    def test_uppercase_validator_init(self):
        validator = user.validators.UppercaseValidator()
        self.assertEqual(validator.min_count, 1)
        self.assertEqual(validator.code, 'password_no_uppercase')

        validator = user.validators.UppercaseValidator(min_count=3)
        self.assertEqual(validator.min_count, 3)

    def test_uppercase_validator_validate_success(self):
        validator = user.validators.UppercaseValidator(min_count=2)
        validator.validate('PaSsword123')
        validator.validate(
            'TESTINGpassword',
        )

    def test_uppercase_validator_validate_failure(self):
        validator = user.validators.UppercaseValidator(min_count=2)
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 uppercase letters.',
        ):
            validator.validate('password123')

        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 uppercase letters.',
        ):
            validator.validate('Password123!')

    def test_uppercase_validator_validate_non_ascii(self):
        validator = user.validators.UppercaseValidator(min_count=1)
        validator.validate('PÄssword123')
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 1 uppercase letter.',
        ):
            validator.validate('ässword123')

    def test_uppercase_validator_get_help_text(self):
        validator = user.validators.UppercaseValidator(min_count=1)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 1 uppercase letter.',
        )

        validator = user.validators.UppercaseValidator(min_count=2)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 2 uppercase letters.',
        )

    def test_lowercase_validator_init(self):
        validator = user.validators.LowercaseValidator()
        self.assertEqual(validator.min_count, 1)
        self.assertEqual(validator.code, 'password_no_lowercase')

        validator = user.validators.LowercaseValidator(min_count=3)
        self.assertEqual(validator.min_count, 3)

    def test_lowercase_validator_validate_success(self):
        validator = user.validators.LowercaseValidator(min_count=2)
        validator.validate('password123')
        validator.validate('PASSWORDtest')

    def test_lowercase_validator_validate_failure(self):
        validator = user.validators.LowercaseValidator(min_count=2)
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 lowercase letters.',
        ):
            validator.validate('PASSWORD123')

        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 lowercase letters.',
        ):
            validator.validate('PAsSWORD123!')

    def test_lowercase_validator_validate_non_ascii(self):
        validator = user.validators.LowercaseValidator(min_count=1)
        validator.validate('pAssword123')
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 1 lowercase letter.',
        ):
            validator.validate(
                'PASSWORd123',
            )
            validator.validate('PASSWORD')

    def test_lowercase_validator_get_help_text(self):
        validator = user.validators.LowercaseValidator(min_count=1)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 1 lowercase letter.',
        )

        validator = user.validators.LowercaseValidator(min_count=2)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 2 lowercase letters.',
        )

    def test_numeric_validator_init(self):
        validator = user.validators.NumericValidator()
        self.assertEqual(validator.min_count, 1)
        self.assertEqual(validator.code, 'password_no_number')

        validator = user.validators.NumericValidator(min_count=3)
        self.assertEqual(validator.min_count, 3)

    def test_numeric_validator_validate_success(self):
        validator = user.validators.NumericValidator(min_count=2)
        validator.validate('password123')
        validator.validate('123abc456')

    def test_numeric_validator_validate_failure(self):
        validator = user.validators.NumericValidator(min_count=2)
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 digits.',
        ):
            validator.validate('password')

        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 digits.',
        ):
            validator.validate('password1')

    def test_numeric_validator_get_help_text(self):
        validator = user.validators.NumericValidator(min_count=1)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 1 digit.',
        )

        validator = user.validators.NumericValidator(min_count=2)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 2 digits.',
        )

    def test_special_character_validator_init(self):
        validator = user.validators.SpecialCharacterValidator()
        self.assertEqual(validator.min_count, 1)
        self.assertEqual(validator.code, 'password_no_special_char')
        self.assertEqual(
            validator.pattern.pattern,
            user.validators.SpecialCharacterValidator.DEFAULT_SPECIAL_CHARS,
        )

        validator = user.validators.SpecialCharacterValidator(
            min_count=3,
            special_chars=r'[@#$]',
        )
        self.assertEqual(validator.min_count, 3)
        self.assertEqual(validator.pattern.pattern, r'[@#$]')

    def test_special_character_validator_validate_success(self):
        validator = user.validators.SpecialCharacterValidator(min_count=2)
        validator.validate('password!@')
        validator.validate('test$%^&')

        custom_validator = user.validators.SpecialCharacterValidator(
            min_count=1,
            special_chars=r'[!@#]',
        )
        custom_validator.validate('password!')
        custom_validator.validate('password@')
        custom_validator.validate('password#')

    def test_special_character_validator_validate_failure(self):
        validator = user.validators.SpecialCharacterValidator(min_count=2)
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 special characters.',
        ):
            validator.validate('password')

        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 2 special characters.',
        ):
            validator.validate('password!')

        custom_validator = user.validators.SpecialCharacterValidator(
            min_count=1,
            special_chars=r'[!@#]',
        )
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password must contain at least 1 special character.',
        ):
            custom_validator.validate('password$')

    def test_special_character_validator_get_help_text(self):
        validator = user.validators.SpecialCharacterValidator(min_count=1)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 1 special character.',
        )

        validator = user.validators.SpecialCharacterValidator(min_count=2)
        self.assertEqual(
            validator.get_help_text(),
            'Your password must contain at least 2 special characters.',
        )

    def test_ascii_validator_init(self):
        validator = user.validators.AsciiValidator()
        self.assertEqual(validator.code, 'password_not_ascii')

    def test_ascii_validator_validate_success(self):
        validator = user.validators.AsciiValidator()
        validator.validate('password123!@#')

    def test_ascii_validator_validate_failure(self):
        validator = user.validators.AsciiValidator()
        with self.assertRaisesMessage(
            django.core.exceptions.ValidationError,
            'Password contains non-ASCII characters.',
        ):
            validator.validate('passwordñ')

    def test_ascii_validator_get_help_text(self):
        validator = user.validators.AsciiValidator()
        self.assertEqual(
            validator.get_help_text(),
            (
                'Your password must only contain standard English letters,'
                ' digits, and symbols.'
            ),
        )
