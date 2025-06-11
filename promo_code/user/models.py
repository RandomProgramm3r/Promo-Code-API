import uuid

import django.contrib.auth.models
import django.db.models
import django.utils.timezone

import business.models
import user.constants


class UserManager(django.contrib.auth.models.BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            surname=surname,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        name,
        surname,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, surname, password, **extra_fields)


class User(
    django.contrib.auth.models.AbstractBaseUser,
    django.contrib.auth.models.PermissionsMixin,
):
    id = django.db.models.UUIDField(
        'UUID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = django.db.models.EmailField(
        unique=True,
        max_length=user.constants.EMAIL_MAX_LENGTH,
    )
    name = django.db.models.CharField(
        max_length=user.constants.NAME_MAX_LENGTH,
    )
    surname = django.db.models.CharField(
        max_length=user.constants.SURNAME_MAX_LENGTH,
    )
    avatar_url = django.db.models.URLField(
        blank=True,
        null=True,
        max_length=user.constants.AVATAR_URL_MAX_LENGTH,
    )
    other = django.db.models.JSONField(default=dict)

    token_version = django.db.models.IntegerField(default=0)

    is_active = django.db.models.BooleanField(default=True)
    is_staff = django.db.models.BooleanField(default=False)
    last_login = django.db.models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.pk:
            self.last_login = django.utils.timezone.now()

        super().save(*args, **kwargs)


class PromoLike(django.db.models.Model):
    id = django.db.models.UUIDField(
        'UUID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = django.db.models.ForeignKey(
        User,
        on_delete=django.db.models.CASCADE,
        related_name='promo_likes',
    )
    promo = django.db.models.ForeignKey(
        business.models.Promo,
        on_delete=django.db.models.CASCADE,
        related_name='likes',
    )
    created_at = django.db.models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            django.db.models.UniqueConstraint(
                fields=['user', 'promo'],
                name='unique_like',
            ),
        ]

    def __str__(self):
        return f'{self.user} likes {self.promo}'


class PromoComment(django.db.models.Model):
    id = django.db.models.UUIDField(
        'UUID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    promo = django.db.models.ForeignKey(
        business.models.Promo,
        on_delete=django.db.models.CASCADE,
        related_name='comments',
    )
    author = django.db.models.ForeignKey(
        User,
        on_delete=django.db.models.CASCADE,
        related_name='comments',
    )
    text = django.db.models.TextField(
        max_length=user.constants.COMMENT_TEXT_MAX_LENGTH,
    )

    created_at = django.db.models.DateTimeField(
        default=django.utils.timezone.now,
        editable=False,
    )
    updated_at = django.db.models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.email} on promo {self.promo.id}'
