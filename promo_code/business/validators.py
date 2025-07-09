import rest_framework.exceptions

import business.constants


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
                    'used_count': self.instance.used_count,
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
        used_count = self.full_data.get('used_count')

        if mode not in [
            business.constants.PROMO_MODE_COMMON,
            business.constants.PROMO_MODE_UNIQUE,
        ]:
            raise rest_framework.exceptions.ValidationError(
                {'mode': 'Invalid mode.'},
            )

        if used_count and used_count > max_count:
            raise rest_framework.exceptions.ValidationError(
                {'mode': 'Invalid max_count.'},
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
                <= max_count
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

        return self.full_data
