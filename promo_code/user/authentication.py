import business.models
import rest_framework_simplejwt.authentication
import rest_framework_simplejwt.exceptions

import user.models as user_models


class CustomJWTAuthentication(
    rest_framework_simplejwt.authentication.JWTAuthentication,
):
    def authenticate(self, request):
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
                'user': (user_models.User, 'user_id'),
                'company': (business.models.Company, 'company_id'),
            }

            if user_type not in model_mapping:
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    'Invalid user type',
                )

            model_class, id_field = model_mapping[user_type]
            instance = model_class.objects.get(
                id=validated_token.get(id_field),
            )
            if instance.token_version != validated_token.get(
                'token_version',
                0,
            ):
                raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                    'Token invalid',
                )

            return (instance, validated_token)

        except (
            user_models.User.DoesNotExist,
            business.models.Company.DoesNotExist,
        ):
            raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                'User or Company not found',
            )
        except rest_framework_simplejwt.exceptions.InvalidToken:
            raise rest_framework_simplejwt.exceptions.AuthenticationFailed(
                'Token is invalid or expired',
            )
