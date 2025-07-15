import pycountry
import rest_framework.exceptions
import rest_framework.serializers

import business.constants
import business.models


class BaseLimitOffsetPaginationSerializer(
    rest_framework.serializers.Serializer,
):
    """
    Base serializer for common filtering and sorting parameters.
    Pagination parameters (limit, offset) are handled by the pagination class.
    """

    limit = rest_framework.serializers.IntegerField(
        min_value=0,
        required=False,
    )
    offset = rest_framework.serializers.IntegerField(
        min_value=0,
        required=False,
    )

    def validate(self, attrs):
        errors = {}
        for field in ('limit', 'offset'):
            raw = self.initial_data.get(field, None)
            if raw == '':
                errors[field] = ['This field cannot be an empty string.']
        if errors:
            raise rest_framework.exceptions.ValidationError(errors)

        return super().validate(attrs)


class CountryField(rest_framework.serializers.CharField):
    """
    Custom field for validating country codes according to ISO 3166-1 alpha-2.
    """

    def __init__(self, **kwargs):
        kwargs['allow_blank'] = False
        kwargs['min_length'] = business.constants.TARGET_COUNTRY_CODE_LENGTH
        kwargs['max_length'] = business.constants.TARGET_COUNTRY_CODE_LENGTH
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        code = super().to_internal_value(data)
        try:
            pycountry.countries.lookup(code.upper())
        except LookupError:
            raise rest_framework.serializers.ValidationError(
                'Invalid ISO 3166-1 alpha-2 country code.',
            )
        return code


class TargetSerializer(rest_framework.serializers.Serializer):
    age_from = rest_framework.serializers.IntegerField(
        min_value=business.constants.TARGET_AGE_MIN,
        max_value=business.constants.TARGET_AGE_MAX,
        required=False,
    )
    age_until = rest_framework.serializers.IntegerField(
        min_value=business.constants.TARGET_AGE_MIN,
        max_value=business.constants.TARGET_AGE_MAX,
        required=False,
    )
    country = CountryField(required=False)

    categories = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.TARGET_CATEGORY_MIN_LENGTH,
            max_length=business.constants.TARGET_CATEGORY_MAX_LENGTH,
            allow_blank=False,
        ),
        max_length=business.constants.TARGET_CATEGORY_MAX_ITEMS,
        required=False,
        allow_empty=True,
    )

    def validate(self, data):
        age_from = data.get('age_from')
        age_until = data.get('age_until')

        if (
            age_from is not None
            and age_until is not None
            and age_from > age_until
        ):
            raise rest_framework.serializers.ValidationError(
                {'age_until': 'Must be greater than or equal to age_from.'},
            )
        return data


class BasePromoSerializer(rest_framework.serializers.ModelSerializer):
    """
    Base serializer for promo, containing validation and representation logic.
    """

    image_url = rest_framework.serializers.URLField(
        required=False,
        allow_blank=False,
        max_length=business.constants.PROMO_IMAGE_URL_MAX_LENGTH,
    )
    description = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_DESC_MIN_LENGTH,
        max_length=business.constants.PROMO_DESC_MAX_LENGTH,
        required=True,
    )
    target = TargetSerializer(
        required=True, allow_null=True,
    )
    promo_common = rest_framework.serializers.CharField(
        min_length=business.constants.PROMO_COMMON_CODE_MIN_LENGTH,
        max_length=business.constants.PROMO_COMMON_CODE_MAX_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=False,
    )
    promo_unique = rest_framework.serializers.ListField(
        child=rest_framework.serializers.CharField(
            min_length=business.constants.PROMO_UNIQUE_CODE_MIN_LENGTH,
            max_length=business.constants.PROMO_UNIQUE_CODE_MAX_LENGTH,
            allow_blank=False,
        ),
        min_length=business.constants.PROMO_UNIQUE_LIST_MIN_ITEMS,
        max_length=business.constants.PROMO_UNIQUE_LIST_MAX_ITEMS,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = business.models.Promo
        fields = (
            'description',
            'image_url',
            'target',
            'max_count',
            'active_from',
            'active_until',
            'mode',
            'promo_common',
            'promo_unique',
        )

    def validate(self, data):
        """
        Main validation method.
        Determines the mode and calls the corresponding validation method.
        """

        mode = data.get('mode', getattr(self.instance, 'mode', None))

        if mode == business.constants.PROMO_MODE_COMMON:
            self._validate_common(data)
        elif mode == business.constants.PROMO_MODE_UNIQUE:
            self._validate_unique(data)
        elif mode is None:
            raise rest_framework.serializers.ValidationError(
                {'mode': 'This field is required.'},
            )
        else:
            raise rest_framework.serializers.ValidationError(
                {'mode': 'Invalid mode.'},
            )

        return data

    def _validate_common(self, data):
        """
        Validations for COMMON promo mode.
        """

        if 'promo_unique' in data and data['promo_unique'] is not None:
            raise rest_framework.serializers.ValidationError(
                {'promo_unique': 'This field is not allowed for COMMON mode.'},
            )

        if self.instance is None and not data.get('promo_common'):
            raise rest_framework.serializers.ValidationError(
                {'promo_common': 'This field is required for COMMON mode.'},
            )

        new_max_count = data.get('max_count')
        if self.instance and new_max_count is not None:
            used_count = self.instance.get_used_codes_count
            if used_count > new_max_count:
                raise rest_framework.serializers.ValidationError(
                    {
                        'max_count': (
                            f'max_count ({new_max_count}) cannot be less than '
                            f'used_count ({used_count}).'
                        ),
                    },
                )

        effective_max_count = (
            new_max_count
            if new_max_count is not None
            else getattr(self.instance, 'max_count', None)
        )

        min_c = business.constants.PROMO_COMMON_MIN_COUNT
        max_c = business.constants.PROMO_COMMON_MAX_COUNT
        if effective_max_count is not None and not (
            min_c <= effective_max_count <= max_c
        ):
            raise rest_framework.serializers.ValidationError(
                {
                    'max_count': (
                        f'Must be between {min_c} and {max_c} for COMMON mode.'
                    ),
                },
            )

    def _validate_unique(self, data):
        """
        Validations for UNIQUE promo mode.
        """

        if 'promo_common' in data and data['promo_common'] is not None:
            raise rest_framework.serializers.ValidationError(
                {'promo_common': 'This field is not allowed for UNIQUE mode.'},
            )

        if self.instance is None and not data.get('promo_unique'):
            raise rest_framework.serializers.ValidationError(
                {'promo_unique': 'This field is required for UNIQUE mode.'},
            )

        effective_max_count = data.get(
            'max_count',
            getattr(self.instance, 'max_count', None),
        )

        if (
            effective_max_count is not None
            and effective_max_count
            != business.constants.PROMO_UNIQUE_MAX_COUNT
        ):
            raise rest_framework.serializers.ValidationError(
                {
                    'max_count': (
                        'Must be equal to '
                        f'{business.constants.PROMO_UNIQUE_MAX_COUNT} '
                        'for UNIQUE mode.'
                    ),
                },
            )

    def to_representation(self, instance):
        """
        Controls the display of fields in the response.
        """

        data = super().to_representation(instance)

        if not instance.image_url:
            data.pop('image_url', None)

        if instance.mode == business.constants.PROMO_MODE_UNIQUE:
            data.pop('promo_common', None)
            if 'promo_unique' in self.fields and isinstance(
                self.fields['promo_unique'],
                rest_framework.serializers.SerializerMethodField,
            ):
                data['promo_unique'] = self.get_promo_unique(instance)
            else:
                data['promo_unique'] = [
                    code.code for code in instance.unique_codes.all()
                ]
        else:
            data.pop('promo_unique', None)

        return data
