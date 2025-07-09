import django.conf
import django.core.cache
import rest_framework_simplejwt.authentication
import rest_framework_simplejwt.exceptions

import business.models
import user.models


class CustomJWTAuthentication(
    rest_framework_simplejwt.authentication.JWTAuthentication,
):
    def authenticate(self, request):
        """
        Authenticates the user or company based on a JWT token,
        supporting multiple user types.
        Retrieves the appropriate model instance from the token,
        checks token versioning and caches the authenticated instance
        for performance.
        """
        try:
            header = self.get_header(request)
            if header is None:
                return None

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

            validated_token = self.get_validated_token(raw_token)
            user_type = validated_token.get('user_type', 'user')
            model_mapping = {
                'user': (user.models.User, 'user_id'),
                'company': (business.models.Company, 'company_id'),
            }

            if user_type not in model_mapping:
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    'Invalid user type',
                )

            model_class, id_field = model_mapping[user_type]
            instance_id = validated_token.get(id_field)
            token_version = validated_token.get('token_version', 0)

            cache_key = (
                f'auth_instance_{user_type}_{instance_id}_v{token_version}'
            )
            cached_instance = django.core.cache.cache.get(cache_key)

            if cached_instance:
                return (cached_instance, validated_token)

            if instance_id is None:
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    f'Missing {id_field} in token',
                )

            instance = model_class.objects.get(id=instance_id)

            if instance.token_version != token_version:
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    'Token invalid',
                )

            cache_timeout = getattr(
                django.conf.settings,
                'AUTH_INSTANCE_CACHE_TIMEOUT',
                3600,
            )
            django.core.cache.cache.set(
                cache_key,
                instance,
                timeout=cache_timeout,
            )

            return (instance, validated_token)

        except (
            user.models.User.DoesNotExist,
            business.models.Company.DoesNotExist,
        ):
            raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                'User or Company not found',
            )
        except rest_framework_simplejwt.exceptions.InvalidToken:
            raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                'Token is invalid or expired',
            )
