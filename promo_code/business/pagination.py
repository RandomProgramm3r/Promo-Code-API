import rest_framework.exceptions
import rest_framework.pagination
import rest_framework.response


class CustomLimitOffsetPagination(
    rest_framework.pagination.LimitOffsetPagination,
):
    default_limit = 10
    max_limit = 100

    def get_limit(self, request):
        param_limit = request.query_params.get(self.limit_query_param)
        if param_limit is not None:
            try:
                limit = int(param_limit)
                if limit < 0:
                    raise rest_framework.exceptions.ValidationError(
                        'Limit cannot be negative.',
                    )

                if limit == 0:
                    return 0

                if self.max_limit:
                    return min(limit, self.max_limit)

                return limit
            except (TypeError, ValueError):
                pass

        return self.default_limit

    def get_paginated_response(self, data):
        response = rest_framework.response.Response(data)
        response.headers['X-Total-Count'] = str(self.count)
        return response
