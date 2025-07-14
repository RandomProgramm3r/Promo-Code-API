import rest_framework.exceptions
import rest_framework.pagination
import rest_framework.response

import core.serializers


class CustomLimitOffsetPagination(
    rest_framework.pagination.LimitOffsetPagination,
):
    default_limit = 10
    max_limit = 100

    def get_limit(self, request):
        serializer = core.serializers.BaseLimitOffsetPaginationSerializer(
            data=request.query_params,
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        limit = validated_data.get('limit', self.default_limit)

        # Allow 0, otherwise cut by max_limit
        return 0 if limit == 0 else min(limit, self.max_limit)

    def get_paginated_response(self, data):
        response = rest_framework.response.Response(data)
        response.headers['X-Total-Count'] = str(self.count)
        return response
