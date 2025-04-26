import django.contrib.auth.models
import django.db.models

import business.constants
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
    def get_queryset(self):
        return super().get_queryset()

    def with_related(self):
        return (
            self.select_related('company')
            .prefetch_related('unique_codes')
            .only(
                'id',
                'company',
                'description',
                'image_url',
                'target',
                'max_count',
                'active_from',
                'active_until',
                'mode',
                'promo_common',
                'created_at',
                'company__id',
                'company__name',
            )
        )

    def for_company(self, user):
        return self.with_related().filter(company=user)

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

        if promo.mode == business.constants.PROMO_MODE_COMMON:
            promo.promo_common = promo_common
            promo.save(update_fields=['promo_common'])
        elif (
            promo.mode == business.constants.PROMO_MODE_UNIQUE and promo_unique
        ):
            self._create_unique_codes(promo, promo_unique)

        return promo

    def _create_unique_codes(self, promo, codes):
        business.models.PromoCode.objects.bulk_create(
            [
                business.models.PromoCode(promo=promo, code=code)
                for code in codes
            ],
        )
