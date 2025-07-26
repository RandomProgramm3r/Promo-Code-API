import django.db.models
import django.db.transaction
import django.utils.timezone
import rest_framework.exceptions

import business.constants
import business.models
import user.antifraud_service
import user.models


class PromoActivationError(rest_framework.exceptions.APIException):
    """Base exception for all promo code activation errors."""

    status_code = 403
    default_detail = 'Failed to activate promo code.'
    default_code = 'promo_activation_failed'


class TargetingError(PromoActivationError):
    """Error for targeting mismatch."""

    default_detail = 'You do not meet the promotion requirements.'
    default_code = 'targeting_mismatch'


class PromoInactiveError(PromoActivationError):
    """Error if the promo code is inactive."""

    default_detail = 'This promotion is currently inactive.'
    default_code = 'promo_inactive'


class PromoUnavailableError(PromoActivationError):
    """Error if all promo codes have been used."""

    default_detail = (
        'Unfortunately, all codes for this promotion have been used.'
    )
    default_code = 'promo_unavailable'


class AntiFraudError(PromoActivationError):
    """Error from the anti-fraud system."""

    default_detail = 'Activation is blocked by the security system.'
    default_code = 'antifraud_block'


class PromoActivationService:
    """Service to encapsulate promo code activation logic."""

    def __init__(self, user: user.models.User, promo: business.models.Promo):
        self.user = user
        self.promo = promo

    def activate(self) -> str:
        """
        Main method that starts the validation and activation process.
        Returns the promo code on success.
        """
        self._validate_targeting()
        self._validate_is_active()
        self._validate_antifraud()

        return self._issue_promo_code()

    def _validate_targeting(self):
        """Checks if the user matches the promotion's targeting settings."""
        target = self.promo.target

        user_age = self.user.other.get('age')
        user_country = (
            self.user.other.get('country', '').lower()
            if self.user.other.get('country')
            else None
        )

        if target.get('country') and user_country != target['country'].lower():
            raise TargetingError('Country mismatch.')

        if target.get('age_from') and user_age < target['age_from']:
            raise TargetingError('Age mismatch.')

        if target.get('age_until') and user_age > target['age_until']:
            raise TargetingError('Age mismatch.')

    def _validate_is_active(self):
        """Checks if the promo is active and codes are available."""

        if not self.promo.active or not self.promo.is_active:
            raise PromoInactiveError()

    def _validate_antifraud(self):
        """Sends a request to the anti-fraud system."""
        antifraud_response = (
            user.antifraud_service.antifraud_service.get_verdict(
                self.user.email,
                str(self.promo.id),
            )
        )
        if not antifraud_response.get('ok'):
            raise AntiFraudError()

    def _issue_promo_code(self) -> str:
        """
        Issues a promo code in an atomic transaction, updates counters,
        and creates a record in the history.
        """
        try:
            with django.db.transaction.atomic():
                promo_locked = (
                    business.models.Promo.objects.select_for_update().get(
                        id=self.promo.id,
                    )
                )
                promo_code_value = None

                if promo_locked.mode == business.constants.PROMO_MODE_COMMON:
                    if promo_locked.used_count < promo_locked.max_count:
                        promo_locked.used_count = (
                            django.db.models.F('used_count') + 1
                        )
                        promo_locked.save(update_fields=['used_count'])
                        promo_code_value = promo_locked.promo_common
                else:
                    unique_code = promo_locked.unique_codes.filter(
                        is_used=False,
                    ).first()
                    if unique_code:
                        unique_code.is_used = True
                        unique_code.used_at = django.utils.timezone.now()
                        unique_code.save(update_fields=['is_used', 'used_at'])
                        promo_code_value = unique_code.code

                if promo_code_value:
                    user.models.PromoActivationHistory.objects.create(
                        user=self.user,
                        promo=promo_locked,
                    )
                    return promo_code_value

        except business.models.Promo.DoesNotExist:
            raise PromoActivationError('Promo not found.')
