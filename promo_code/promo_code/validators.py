import re

import django.core.exceptions
import django.utils.translation
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Validates that the password contains at least a minimum number of uppercase
    ASCII letters.
    """

    def __init__(self, min_count=1):
        self.min_count = min_count
        self.code = 'password_no_uppercase'

    def validate(self, password, user=None):
        count = sum(
            1 for char in password if char.isupper() and char.isascii()
        )
        if count < self.min_count:
            msg = django.utils.translation.ngettext(
                'Password must contain at least %(min_count)d uppercase '
                'letter.',
                'Password must contain at least %(min_count)d uppercase '
                'letters.',
                self.min_count,
            ) % {
                'min_count': self.min_count,
            }
            raise django.core.exceptions.ValidationError(
                msg,
                code=self.code,
                params={'min_count': self.min_count},
            )

    def get_help_text(self):
        return _(
            'Your password must contain at least %(min_count)d uppercase '
            'letter.'
            if self.min_count == 1
            else 'Your password must contain at least %(min_count)d uppercase '
            'letters.',
        ) % {
            'min_count': self.min_count,
        }


class LowercaseValidator:
    """
    Validates that the password contains at least a minimum number of lowercase
    ASCII letters.
    """

    def __init__(self, min_count=1):
        self.min_count = min_count
        self.code = 'password_no_lowercase'

    def validate(self, password, user=None):
        count = sum(
            1 for char in password if char.islower() and char.isascii()
        )
        if count < self.min_count:
            msg = django.utils.translation.ngettext(
                'Password must contain at least %(min_count)d lowercase '
                'letter.',
                'Password must contain at least %(min_count)d lowercase '
                'letters.',
                self.min_count,
            ) % {
                'min_count': self.min_count,
            }
            raise django.core.exceptions.ValidationError(
                msg,
                code=self.code,
                params={'min_count': self.min_count},
            )

    def get_help_text(self):
        return _(
            'Your password must contain at least %(min_count)d lowercase '
            'letter.'
            if self.min_count == 1
            else 'Your password must contain at least %(min_count)d lowercase '
            'letters.',
        ) % {
            'min_count': self.min_count,
        }


class NumericValidator:
    """
    Validates that the password contains at least a minimum number of digits.
    """

    def __init__(self, min_count=1):
        self.min_count = min_count
        self.code = 'password_no_number'

    def validate(self, password, user=None):
        count = sum(1 for char in password if char.isdigit())
        if count < self.min_count:
            msg = django.utils.translation.ngettext(
                'Password must contain at least %(min_count)d digit.',
                'Password must contain at least %(min_count)d digits.',
                self.min_count,
            ) % {
                'min_count': self.min_count,
            }
            raise django.core.exceptions.ValidationError(
                msg,
                code=self.code,
                params={'min_count': self.min_count},
            )

    def get_help_text(self):
        return _(
            'Your password must contain at least %(min_count)d digit.'
            if self.min_count == 1
            else 'Your password must contain at least %(min_count)d digits.',
        ) % {
            'min_count': self.min_count,
        }


class SpecialCharacterValidator:
    """
    Validates that the password contains at least a minimum number of special
    characters.
    """

    DEFAULT_SPECIAL_CHARS = r'[!@#$%^&*()_+\-\=\[\]{};\':",./<>?`~\\]'

    def __init__(self, min_count=1, special_chars=None):
        self.min_count = min_count
        self.pattern = re.compile(special_chars or self.DEFAULT_SPECIAL_CHARS)
        self.code = 'password_no_special_char'

    def validate(self, password, user=None):
        count = len(self.pattern.findall(password))
        if count < self.min_count:
            msg = django.utils.translation.ngettext(
                'Password must contain at least %(min_count)d special '
                'character.',
                'Password must contain at least %(min_count)d special '
                'characters.',
                self.min_count,
            ) % {
                'min_count': self.min_count,
            }
            raise django.core.exceptions.ValidationError(
                msg,
                code=self.code,
                params={'min_count': self.min_count},
            )

    def get_help_text(self):
        return _(
            'Your password must contain at least %(min_count)d special '
            'character.'
            if self.min_count == 1
            else 'Your password must contain at least %(min_count)d special '
            'characters.',
        ) % {
            'min_count': self.min_count,
        }


class AsciiValidator:
    """
    Validates that the password contains only ASCII characters.
    """

    def __init__(self):
        self.code = 'password_not_ascii'

    def validate(self, password, user=None):
        if not password.isascii():
            raise django.core.exceptions.ValidationError(
                _('Password contains non-ASCII characters.'),
                code=self.code,
            )

    def get_help_text(self):
        return _(
            'Your password must only contain standard English letters, '
            'digits, and symbols.',
        )
