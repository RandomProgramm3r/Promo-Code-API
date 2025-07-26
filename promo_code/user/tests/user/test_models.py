import django.test
import django.utils.timezone

import business.models
import user.models


class UserManagerTests(django.test.TestCase):
    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            user.models.User.objects.create_user(
                email=None,
                name='Test',
                surname='User',
            )

    def test_create_superuser(self):
        user_ = user.models.User.objects.create_superuser(
            email='super@test.com',
            name='Super',
            surname='User',
            password='password123',
        )
        self.assertTrue(user_.is_staff)
        self.assertTrue(user_.is_superuser)
        self.assertEqual(user_.email, 'super@test.com')


class UserModelTests(django.test.TestCase):
    def setUp(self):
        self.user_ = user.models.User.objects.create_user(
            email='test@example.com',
            name='Test',
            surname='User',
            password='password123',
        )

    def test_user_str_representation(self):
        self.assertEqual(str(self.user_), 'test@example.com')


class RelatedModelsStrTests(django.test.TestCase):
    def setUp(self):
        self.user_ = user.models.User.objects.create(
            email='user@test.com',
            name='Test',
            surname='User',
        )
        self.company = business.models.Company.objects.create(
            email='company@test.com',
            name='TestCorp',
        )
        self.promo = business.models.Promo.objects.create(
            company=self.company,
            description='Test Promo',
            max_count=100,
            mode='COMMON',
        )

    def test_promo_like_str(self):
        like = user.models.PromoLike.objects.create(
            user=self.user_,
            promo=self.promo,
        )
        expected_str = f'{self.user_} likes {self.promo}'
        self.assertEqual(str(like), expected_str)

    def test_promo_comment_str(self):
        comment = user.models.PromoComment.objects.create(
            author=self.user_,
            promo=self.promo,
            text='A test comment.',
        )
        expected_str = (
            f'Comment by {self.user_.email} on promo {self.promo.id}'
        )
        self.assertEqual(str(comment), expected_str)

    def test_promo_activation_history_str(self):
        activation = user.models.PromoActivationHistory.objects.create(
            user=self.user_,
            promo=self.promo,
        )
        activation.activated_at = django.utils.timezone.now()
        activation.save()

        expected_str = (
            f'{self.user_} activated {self.promo.id} at '
            f'{activation.activated_at}'
        )
        self.assertEqual(str(activation), expected_str)
