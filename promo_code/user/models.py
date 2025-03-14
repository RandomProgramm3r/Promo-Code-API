import django.contrib.auth.models
import django.db.models
import django.utils.timezone


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
    email = django.db.models.EmailField(unique=True, max_length=120)
    name = django.db.models.CharField(max_length=100)
    surname = django.db.models.CharField(max_length=120)
    avatar_url = django.db.models.URLField(
        blank=True,
        null=True,
        max_length=350,
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
