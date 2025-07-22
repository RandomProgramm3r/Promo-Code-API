import django.contrib.auth.models
import django.db.models
import django.utils.timezone

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
    with_related_fields = (
        'id',
        'company__id',
        'company__name',
        'description',
        'image_url',
        'target',
        'max_count',
        'active_from',
        'active_until',
        'mode',
        'promo_common',
        'created_at',
    )

    def get_queryset(self):
        return super().get_queryset()

    def with_related(self):
        return (
            self.select_related('company')
            .prefetch_related('unique_codes')
            .only(
                *self.with_related_fields,
            )
        )

    def for_company(self, user):
        return self.with_related().filter(company=user)

    def get_feed_for_user(
        self, user, active_filter=None, user_country=None, user_age=None,
    ):
        """
        Retrieve a queryset of Promo objects for a given user, filtered
        and ordered according to specified criteria.
        """
        today = django.utils.timezone.now().date()

        qs = (
            self.get_queryset()
            .select_related('company')
            .annotate(_has_unique_codes=self._q_has_unique_codes())
            .filter(self._q_is_targeted(user_country, user_age))
        )

        if active_filter is not None:
            is_active = active_filter.lower() == 'true'
            active_q = self._q_is_active(today)
            qs = qs.filter(active_q) if is_active else qs.exclude(active_q)

        return qs.order_by('-created_at')

    def _q_is_active(self, today):
        """
        Build a Q expression that checks whether a promo
        is active on the given date.
        """

        qt = django.db.models.Q(active_from__lte=today) | django.db.models.Q(
            active_from__isnull=True,
        )
        tu = django.db.models.Q(active_until__gte=today) | django.db.models.Q(
            active_until__isnull=True,
        )

        common = django.db.models.Q(
            mode=business.constants.PROMO_MODE_COMMON,
            used_count__lt=django.db.models.F('max_count'),
        )
        unique = django.db.models.Q(
            mode=business.constants.PROMO_MODE_UNIQUE, _has_unique_codes=True,
        )

        return qt & tu & (common | unique)

    def _q_has_unique_codes(self):
        """
        Annotate whether there are unused unique codes remaining
        for each promo.
        """
        subq = business.models.PromoCode.objects.filter(
            promo=django.db.models.OuterRef('pk'), is_used=False,
        )
        return django.db.models.Exists(subq)

    def _q_is_targeted(self, country, age):
        """
        Build a Q expression that checks whether a promo targets the given
        country and age, or is not targeted.
        """
        empty = django.db.models.Q(target={})

        if country:
            match_country = django.db.models.Q(target__country__iexact=country)
        else:
            match_country = django.db.models.Q()
        no_country = ~django.db.models.Q(
            target__has_key='country',
        ) | django.db.models.Q(target__country__isnull=True)
        country_ok = match_country | no_country

        no_age_limits = ~django.db.models.Q(
            target__has_key='age_from',
        ) & ~django.db.models.Q(target__has_key='age_until')
        if age is None:
            age_ok = no_age_limits
        else:
            from_ok = (
                ~django.db.models.Q(target__has_key='age_from')
                | django.db.models.Q(target__age_from__isnull=True)
                | django.db.models.Q(target__age_from__lte=age)
            )
            until_ok = (
                ~django.db.models.Q(target__has_key='age_until')
                | django.db.models.Q(target__age_until__isnull=True)
                | django.db.models.Q(target__age_until__gte=age)
            )
            age_ok = no_age_limits | (from_ok & until_ok)

        return empty | (country_ok & age_ok)

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
