import abc
import re

import django.core.exceptions
from django.utils.translation import gettext as _


class BaseCountPasswordValidator(abc.ABC):
    """
    Abstract base class for password validators checking
    character count requirements.

    Attributes:
        min_count (int): Minimum required character count (>=1)

    Raises:
        ValueError: If min_count is less than 1 during initialization
    """

    def __init__(self, min_count=1):
        if min_count < 1:
            raise ValueError('min_count must be at least 1')

        self.min_count = min_count

    @abc.abstractmethod
    def get_help_text(self) -> str:
        """Abstract method to return user-friendly help text"""
        pass

    def validate(self, password, user=None):
        """
        Validate password meets the character count requirement

        Args:
            password (str): Password to validate
            user (User): Optional user object (not used)

        Raises:
            ValidationError: If validation fails
        """
        count = sum(1 for char in password if self.validate_char(char))
        if count < self.min_count:
            raise django.core.exceptions.ValidationError(
                self.get_error_message(),
                code=self.get_code(),
            )

    def validate_char(self, char) -> bool:
        """
        Check if character meets validation criteria

        Args:
            char (str): Single character to check

        Returns:
            bool: Validation result
        """
        raise NotImplementedError

    def get_code(self) -> str:
        """Get error code identifier"""
        return getattr(self, 'code', 'base_code')

    def get_error_message(self) -> str:
        """Get localized error message"""
        raise NotImplementedError


class SpecialCharacterPasswordValidator(BaseCountPasswordValidator):
    """
    Validates presence of minimum required special characters

    Args:
        special_chars (str): Regex pattern for valid special characters
        min_count (int): Minimum required count (default: 1)

    Example:
        SpecialCharacterValidator(r'[!@#$%^&*]', min_count=2)
    """

    def __init__(
        self,
        special_chars=r'[!@#$%^&*()_+\-=\[\]{};\':",./<>?`~\\]',
        min_count=1,
    ):
        super().__init__(min_count)
        self.pattern = re.compile(special_chars)
        self.code = 'password_no_special_char'

    def validate_char(self, char) -> bool:
        """Check if character matches special characters pattern"""
        return bool(self.pattern.match(char))

    def get_help_text(self) -> str:
        return _(
            (
                f'Your password must contain at least {self.min_count} '
                'special character(s).'
            ),
        )

    def get_error_message(self) -> str:
        return _(
            (
                f'Password must contain at least {self.min_count} '
                'special character(s).'
            ),
        )


class NumericPasswordValidator(BaseCountPasswordValidator):
    """
    Validates presence of minimum required numeric digits

    Args:
        min_count (int): Minimum required digits (default: 1)
    """

    def __init__(self, min_count=1):
        super().__init__(min_count)
        self.code = 'password_no_number'

    def validate_char(self, char) -> bool:
        """Check if character is a digit"""
        return char.isdigit()

    def get_help_text(self) -> str:
        return _(
            f'Your password must contain at least {self.min_count} digit(s).',
        )

    def get_error_message(self) -> str:
        return _(f'Password must contain at least {self.min_count} digit(s).')


class LowercaseLatinLetterPasswordValidator(BaseCountPasswordValidator):
    """
    Validates presence of minimum required lowercase Latin letters

    Args:
        min_count (int): Minimum required lowercase letters (default: 1)
    """

    def __init__(self, min_count=1):
        super().__init__(min_count)
        self.code = 'password_no_lowercase_latin'

    def validate_char(self, char) -> bool:
        """Check if character is lower Latin letter"""
        return char.islower() and char.isascii()

    def get_help_text(self) -> str:
        return _(
            (
                f'Your password must contain at least {self.min_count} '
                'lowercase Latin letter(s).'
            ),
        )

    def get_error_message(self) -> str:
        return _(
            (
                f'Password must contain at least {self.min_count} '
                'lowercase Latin letter(s).'
            ),
        )


class UppercaseLatinLetterPasswordValidator(BaseCountPasswordValidator):
    """
    Validates presence of minimum required uppercase Latin letters

    Args:
        min_count (int): Minimum required uppercase letters (default: 1)
    """

    def __init__(self, min_count=1):
        super().__init__(min_count)
        self.code = 'password_no_uppercase_latin'

    def validate_char(self, char) -> bool:
        """Check if character is uppercase Latin letter"""
        return char.isupper() and char.isascii()

    def get_help_text(self) -> str:
        return _(
            (
                f'Your password must contain at least {self.min_count} '
                'uppercase Latin letter(s).'
            ),
        )

    def get_error_message(self) -> str:
        return _(
            (
                f'Password must contain at least {self.min_count} '
                'uppercase Latin letter(s).'
            ),
        )


class ASCIIOnlyPasswordValidator:
    """
    Validates that password contains only ASCII characters

    Example:
    - Valid: 'Passw0rd!123'
    - Invalid: 'Pässwörd§123'
    """

    code = 'password_not_only_ascii_characters'

    def validate(self, password, user=None) -> bool:
        try:
            password.encode('ascii', errors='strict')
        except UnicodeEncodeError:
            raise django.core.exceptions.ValidationError(
                _('Password contains non-ASCII characters'),
                code=self.code,
            )

    def get_help_text(self) -> str:
        return _(
            (
                'Your password must contain only standard English letters, '
                'digits and punctuation symbols (ASCII character set)'
            ),
        )

    def get_error_message(self) -> str:
        return _(
            (
                'Your password must contain only standard English letters, '
                'digits and punctuation symbols (ASCII character set)'
            ),
        )
