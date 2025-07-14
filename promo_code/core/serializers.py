import rest_framework.exceptions
import rest_framework.serializers


class BaseLimitOffsetPaginationSerializer(
    rest_framework.serializers.Serializer,
):
    """
    Base serializer for common filtering and sorting parameters.
    Pagination parameters (limit, offset) are handled by the pagination class.
    """

    limit = rest_framework.serializers.IntegerField(
        min_value=0,
        required=False,
    )
    offset = rest_framework.serializers.IntegerField(
        min_value=0,
        required=False,
    )

    def validate(self, attrs):
        errors = {}
        for field in ('limit', 'offset'):
            raw = self.initial_data.get(field, None)
            if raw == '':
                errors[field] = ['This field cannot be an empty string.']
        if errors:
            raise rest_framework.exceptions.ValidationError(errors)

        return super().validate(attrs)
