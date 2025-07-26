import unittest.mock

import django.test

import business.constants
import business.models
import user.models
import user.services


@unittest.mock.patch(
    'user.antifraud_service.antifraud_service.get_verdict',
    return_value={'ok': True},
)
class PromoActivationServiceTestCase(django.test.TestCase):
    def setUp(self):
        self.user_ = user.models.User.objects.create_user(
            name='John',
            surname='Jones',
            email='test@example.com',
            password='password123',
            other={'country': 'lu', 'age': 30},
        )
        self.promo = business.models.Promo.objects.create(
            description='Test Promo',
            active=True,
            target={'country': 'lu', 'age_from': 20, 'age_until': 40},
            mode=business.constants.PROMO_MODE_COMMON,
            max_count=100,
            used_count=0,
            promo_common='COMMON_CODE',
        )

    def test_targeting_fails_if_age_from_and_user_age_is_none(
        self,
        mock_antifraud,
    ):
        self.user_.other = {'country': 'lu', 'age': 30}
        self.user_.save()
        self.promo.target = {'age_until': 25}
        self.promo.save()

        service = user.services.PromoActivationService(
            user=self.user_,
            promo=self.promo,
        )

        with self.assertRaisesRegex(
            user.services.TargetingError,
            'Age mismatch.',
        ):
            service.activate()

    def test_targeting_fails_if_age_until_mismatch(self, mock_antifraud):
        self.promo.target = {'age_until': 25}
        self.promo.save()

        service = user.services.PromoActivationService(
            user=self.user_,
            promo=self.promo,
        )

        with self.assertRaisesRegex(
            user.services.TargetingError,
            'Age mismatch.',
        ):
            service.activate()

    def test_targeting_fails_if_age_from_mismatch(self, mock_antifraud):
        self.promo.target = {'age_from': 31}
        self.promo.save()

        service = user.services.PromoActivationService(
            user=self.user_,
            promo=self.promo,
        )

        with self.assertRaisesRegex(
            user.services.TargetingError,
            'Age mismatch.',
        ):
            service.activate()

    def test_activation_fails_if_promo_deleted_mid_process(
        self,
        mock_antifraud,
    ):
        service = user.services.PromoActivationService(
            user=self.user_,
            promo=self.promo,
        )

        self.promo.delete()

        with self.assertRaisesRegex(
            user.services.PromoActivationError,
            'Promo not found.',
        ):
            service.activate()
