import pycountry
import rest_framework.exceptions
import rest_framework.serializers

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


class OtherFieldValidator(rest_framework.serializers.Serializer):
    """
    Validates JSON fields:
    - age (required, 0-100)
    - country (required, valid ISO 3166-1 alpha-2)
    """

    country_codes = {c.alpha_2 for c in pycountry.countries}
    print(country_codes)

    age = rest_framework.serializers.IntegerField(
        required=True,
        min_value=0,
        max_value=100,
        error_messages={
            'required': 'This field is required.',
            'invalid': 'Must be an integer.',
            'min_value': 'Must be between 0 and 100.',
            'max_value': 'Must be between 0 and 100.',
        },
    )

    country = rest_framework.serializers.CharField(
        required=True,
        max_length=2,
        min_length=2,
        error_messages={
            'required': 'This field is required.',
            'blank': 'Must be a 2-letter ISO code.',
            'max_length': 'Must be a 2-letter ISO code.',
            'min_length': 'Must be a 2-letter ISO code.',
        },
    )

    def validate_country(self, value):
        country = value.upper()
        if country not in self.country_codes:
            raise rest_framework.serializers.ValidationError(
                'Invalid ISO 3166-1 alpha-2 country code.',
            )

        return country

    def __call__(self, value):
        if not isinstance(value, dict):
            raise rest_framework.serializers.ValidationError(
                {'non_field_errors': ['Must be a JSON object']},
            )

        missing_fields = [
            field
            for field in self.fields
            if field not in value or value.get(field) in (None, '')
        ]

        if missing_fields:
            raise rest_framework.serializers.ValidationError(
                {field: 'This field is required.' for field in missing_fields},
            )

        serializer = self.__class__(data=value)
        if not serializer.is_valid():
            raise rest_framework.serializers.ValidationError(serializer.errors)

        return value
