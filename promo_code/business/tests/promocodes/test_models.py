import django.test

import business.constants
import business.models


class CompanyModelTests(django.test.TestCase):
    def test_company_str_representation(self):
        company = business.models.Company.objects.create(
            email='contact@company.com',
            name='My Awesome Company',
        )
        self.assertEqual(str(company), 'My Awesome Company')


class PromoModelTests(django.test.TestCase):
    def setUp(self):
        self.company = business.models.Company.objects.create(
            email='company@test.com',
            name='TestCorp',
        )
        self.common_promo = business.models.Promo.objects.create(
            company=self.company,
            description='A common promo',
            max_count=100,
            used_count=50,
            mode=business.constants.PROMO_MODE_COMMON,
        )

    def test_promo_str_representation(self):
        expected_str = (
            f'Promo {self.common_promo.id} ({self.common_promo.mode})'
        )
        self.assertEqual(str(self.common_promo), expected_str)


class PromoCodeModelTests(django.test.TestCase):
    def test_promo_code_str_representation(self):
        company = business.models.Company.objects.create(
            email='company@test.com',
            name='TestCorp',
        )
        promo = business.models.Promo.objects.create(
            company=company,
            description='Unique codes promo',
            max_count=10,
            mode=business.constants.PROMO_MODE_UNIQUE,
        )
        promo_code = business.models.PromoCode.objects.create(
            promo=promo,
            code='UNIQUE123',
        )
        self.assertEqual(str(promo_code), 'UNIQUE123')
