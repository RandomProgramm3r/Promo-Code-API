import pycountry
import rest_framework.exceptions

import user.models


class UniqueEmailValidator:
    def __init__(self, default_detail=None, default_code=None):
        self.status_code = 409
        self.default_detail = (
            default_detail or 'This email address is already registered.'
        )
        self.default_code = default_code or 'email_conflict'

    def __call__(self, value):
        if user.models.User.objects.filter(email=value).exists():
            exc = rest_framework.exceptions.APIException(
                detail={
                    'status': 'error',
                    'message': self.default_detail,
                    'code': self.default_code,
                },
            )
            exc.status_code = self.status_code
            raise exc


class OtherFieldValidator:
    """
    Validator for JSON fields containing:
    - age (required, integer between 0 and 100)
    - country (required, string with an ISO 3166-1 alpha-2 country code)
    """

    error_messages = {
        'invalid_type': 'Must be a JSON object.',
        'missing_field': 'This field is required.',
        'age_type': 'Must be an integer.',
        'age_range': 'Must be between 0 and 100.',
        'country_format': 'Must be a 2-letter ISO code.',
        'country_invalid': 'Invalid ISO 3166-1 alpha-2 country code.',
    }

    def __call__(self, value):
        if not isinstance(value, dict):
            raise rest_framework.exceptions.ValidationError(
                self.error_messages['invalid_type'],
            )

        errors = {}

        # Validate the 'age' field
        age = value.get('age')
        if age is None:
            errors['age'] = self.error_messages['missing_field']
        elif not isinstance(age, int):
            errors['age'] = self.error_messages['age_type']
        elif not (0 <= age <= 100):
            errors['age'] = self.error_messages['age_range']

        # Validate the 'country' field
        country_code = value.get('country')
        if country_code is None:
            errors['country'] = self.error_messages['missing_field']
        elif not (isinstance(country_code, str) and len(country_code) == 2):
            errors['country'] = self.error_messages['country_format']
        elif not pycountry.countries.get(alpha_2=country_code.upper()):
            errors['country'] = self.error_messages['country_invalid']

        if errors:
            raise rest_framework.exceptions.ValidationError(errors)
