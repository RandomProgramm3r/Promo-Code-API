import django.core.cache
import django.db.models


def bump_token_version(
    instance: django.db.models.Model,
) -> django.db.models.Model:
    """
    Atomically increments token_version for any model instance
    (User or Company), invalidates the corresponding cache,
    and returns the updated instance.
    """
    user_type = instance.__class__.__name__.lower()

    old_token_version = instance.token_version

    instance.__class__.objects.filter(id=instance.id).update(
        token_version=django.db.models.F('token_version') + 1,
    )

    old_cache_key = (
        f'auth_instance_{user_type}_{instance.id}_v{old_token_version}'
    )
    django.core.cache.cache.delete(old_cache_key)

    instance.refresh_from_db()

    return instance
