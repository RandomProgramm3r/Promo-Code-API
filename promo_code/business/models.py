import uuid

import django.contrib.auth.models
import django.db.models
import django.utils.timezone

import business.constants
import business.managers


class Company(django.contrib.auth.models.AbstractBaseUser):
    id = django.db.models.UUIDField(
        'UUID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = django.db.models.EmailField(
        unique=True,
        max_length=business.constants.COMPANY_EMAIL_MAX_LENGTH,
    )
    name = django.db.models.CharField(
        max_length=business.constants.COMPANY_NAME_MAX_LENGTH,
    )

    token_version = django.db.models.IntegerField(default=0)
    created_at = django.db.models.DateTimeField(auto_now_add=True)
    is_active = django.db.models.BooleanField(default=True)

    objects = business.managers.CompanyManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name


class Promo(django.db.models.Model):
    id = django.db.models.UUIDField(
        'UUID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = django.db.models.ForeignKey(
        Company,
        on_delete=django.db.models.CASCADE,
        null=True,
        blank=True,
    )
    description = django.db.models.CharField(
        max_length=business.constants.PROMO_DESC_MAX_LENGTH,
    )
    image_url = django.db.models.URLField(
        max_length=business.constants.PROMO_IMAGE_URL_MAX_LENGTH,
        blank=True,
        null=True,
    )
    target = django.db.models.JSONField(default=dict)
    max_count = django.db.models.IntegerField()
    active_from = django.db.models.DateField(null=True, blank=True)
    active_until = django.db.models.DateField(null=True, blank=True)
    mode = django.db.models.CharField(
        max_length=10,
        choices=business.constants.PROMO_MODE_CHOICES,
    )
    promo_common = django.db.models.CharField(
        max_length=business.constants.PROMO_COMMON_CODE_MAX_LENGTH,
        blank=True,
        null=True,
    )
    active = django.db.models.BooleanField(default=True)

    created_at = django.db.models.DateTimeField(auto_now_add=True)

    objects = business.managers.PromoManager()

    def __str__(self):
        return f'Promo {self.id} ({self.mode})'

    @property
    def is_active(self) -> bool:
        today = django.utils.timezone.timezone.now().date()
        if self.active_from and self.active_from > today:
            return False
        if self.active_until and self.active_until < today:
            return False

        if self.mode == business.constants.PROMO_MODE_UNIQUE:
            return self.unique_codes.filter(is_used=False).exists()
        # TODO: COMMON Promo
        return True

    @property
    def get_used_codes_count(self) -> int:
        if self.mode == business.constants.PROMO_MODE_UNIQUE:
            return self.unique_codes.filter(is_used=True).count()
        # TODO: COMMON Promo
        return 0

    @property
    def get_available_unique_codes(self) -> list[str] | None:
        if self.mode == business.constants.PROMO_MODE_UNIQUE:
            return [c.code for c in self.unique_codes.filter(is_used=False)]
        return None


class PromoCode(django.db.models.Model):
    promo = django.db.models.ForeignKey(
        Promo,
        on_delete=django.db.models.CASCADE,
        related_name='unique_codes',
        to_field='id',
    )
    code = django.db.models.CharField(
        max_length=business.constants.PROMO_UNIQUE_CODE_MAX_LENGTH,
    )
    is_used = django.db.models.BooleanField(default=False)
    used_at = django.db.models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('promo', 'code')

    def __str__(self):
        return self.code
