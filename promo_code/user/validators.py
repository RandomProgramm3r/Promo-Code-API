import rest_framework.exceptions

import user.models


class UniqueEmailValidator:
    def __init__(self, default_detail=None, default_code=None):
        self.status_code = 409
        self.default_detail = (
            default_detail or 'This email address is already registered.'
        )
        self.default_code = default_code or 'email_conflict'

    def __call__(self, value):
        if user.models.User.objects.filter(email=value).exists():
            exc = rest_framework.exceptions.APIException(
                detail={
                    'status': 'error',
                    'message': self.default_detail,
                    'code': self.default_code,
                },
            )
            exc.status_code = self.status_code
            raise exc
