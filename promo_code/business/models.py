import django.contrib.auth.models
import django.db.models


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


class Company(django.contrib.auth.models.AbstractBaseUser):
    email = django.db.models.EmailField(
        unique=True,
        max_length=120,
    )
    name = django.db.models.CharField(max_length=50)

    token_version = django.db.models.IntegerField(default=0)
    created_at = django.db.models.DateTimeField(auto_now_add=True)
    is_active = django.db.models.BooleanField(default=True)

    objects = CompanyManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name
