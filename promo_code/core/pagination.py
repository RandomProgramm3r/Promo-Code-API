import rest_framework.pagination
import rest_framework.response


class CustomLimitOffsetPagination(
    rest_framework.pagination.LimitOffsetPagination,
):
    default_limit = 10
    max_limit = 100

    def get_limit(self, request):
        raw_limit = request.query_params.get(self.limit_query_param)

        if raw_limit is None:
            return self.default_limit

        limit = int(raw_limit)

        # Allow 0, otherwise cut by max_limit
        return 0 if limit == 0 else min(limit, self.max_limit)

    def get_paginated_response(self, data):
        response = rest_framework.response.Response(data)
        response.headers['X-Total-Count'] = str(self.count)
        return response
