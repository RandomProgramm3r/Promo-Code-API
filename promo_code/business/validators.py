import rest_framework.exceptions

import business.constants
import business.models


class UniqueEmailValidator:
    def __init__(self, default_detail=None, default_code=None):
        self.status_code = 409
        self.default_detail = (
            default_detail or 'This email address is already registered.'
        )
        self.default_code = default_code or 'email_conflict'

    def __call__(self, value):
        if business.models.Company.objects.filter(email=value).exists():
            exc = rest_framework.exceptions.APIException(
                detail={
                    'status': 'error',
                    'message': self.default_detail,
                    'code': self.default_code,
                },
            )
            exc.status_code = self.status_code
            raise exc


class PromoValidator:
    def __init__(self, data, instance=None):
        self.data = data
        self.instance = instance
        self.full_data = self._get_full_data()

    def _get_full_data(self):
        full_data = {}
        if self.instance is not None:
            full_data.update(
                {
                    'mode': self.instance.mode,
                    'promo_common': self.instance.promo_common,
                    'promo_unique': None,
                    'max_count': self.instance.max_count,
                    'active_from': self.instance.active_from,
                    'active_until': self.instance.active_until,
                    'target': self.instance.target
                    if self.instance.target
                    else {},
                },
            )

        full_data.update(self.data)
        return full_data

    def validate(self):
        mode = self.full_data.get('mode')
        promo_common = self.full_data.get('promo_common')
        promo_unique = self.full_data.get('promo_unique')
        max_count = self.full_data.get('max_count')
        active_from = self.full_data.get('active_from')
        active_until = self.full_data.get('active_until')

        if mode not in [
            business.constants.PROMO_MODE_COMMON,
            business.constants.PROMO_MODE_UNIQUE,
        ]:
            raise rest_framework.exceptions.ValidationError(
                {'mode': 'Invalid mode.'},
            )

        if mode == business.constants.PROMO_MODE_COMMON:
            if not promo_common:
                raise rest_framework.exceptions.ValidationError(
                    {
                        'promo_common': (
                            'This field is required for COMMON mode.'
                        ),
                    },
                )
            if promo_unique is not None:
                raise rest_framework.exceptions.ValidationError(
                    {
                        'promo_unique': (
                            'This field is not allowed for COMMON mode.'
                        ),
                    },
                )
            if max_count is None or not (
                business.constants.PROMO_COMMON_MIN_COUNT
                < max_count
                <= business.constants.PROMO_COMMON_MAX_COUNT
            ):
                raise rest_framework.exceptions.ValidationError(
                    {
                        'max_count': (
                            'Must be between 0 and 100,000,000 '
                            'for COMMON mode.'
                        ),
                    },
                )

        elif mode == business.constants.PROMO_MODE_UNIQUE:
            if promo_common is not None:
                raise rest_framework.exceptions.ValidationError(
                    {
                        'promo_common': (
                            'This field is not allowed for UNIQUE mode.'
                        ),
                    },
                )
            if max_count != business.constants.PROMO_UNIQUE_MAX_COUNT:
                raise rest_framework.exceptions.ValidationError(
                    {'max_count': 'Must be 1 for UNIQUE mode.'},
                )

        if active_from and active_until and active_from > active_until:
            raise rest_framework.exceptions.ValidationError(
                {'active_until': 'Must be after or equal to active_from.'},
            )

        return self.full_data
