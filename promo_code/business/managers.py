import django.contrib.auth.models
import django.db.models

import business.models


class CompanyManager(django.contrib.auth.models.BaseUserManager):
    def create_company(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')

        email = self.normalize_email(email)
        company = self.model(
            email=email,
            name=name,
            **extra_fields,
        )
        company.set_password(password)
        company.save(using=self._db)
        return company


class PromoManager(django.db.models.Manager):
    @django.db.transaction.atomic
    def create_promo(
        self,
        user,
        target_data,
        promo_common,
        promo_unique,
        **kwargs,
    ):
        promo = self.create(
            company=user,
            target=target_data,
            **kwargs,
        )

        if promo.mode == business.models.Promo.MODE_COMMON:
            promo.promo_common = promo_common
            promo.save(update_fields=['promo_common'])
        elif promo.mode == business.models.Promo.MODE_UNIQUE and promo_unique:
            self._create_unique_codes(promo, promo_unique)

        return promo

    def _create_unique_codes(self, promo, codes):
        business.models.PromoCode.objects.bulk_create(
            [
                business.models.PromoCode(promo=promo, code=code)
                for code in codes
            ],
        )
