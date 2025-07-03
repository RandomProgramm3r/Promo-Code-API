import datetime
import json
import typing

import django.conf
import django.core.cache
import requests
import requests.exceptions


class AntiFraudService:
    """
    A service class to interact with the anti-fraud system.

    Encapsulates caching, HTTP requests, and error handling.
    """

    def __init__(
        self,
        base_url: str = django.conf.settings.ANTIFRAUD_VALIDATE_URL,
        timeout: int = 5,
        max_retries: int = 2,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def get_verdict(self, user_email: str, promo_id: str) -> typing.Dict:
        """
        Retrieves the anti-fraud verdict for a given user and promo.

        1. Checks the cache.
        2. If not in cache, fetches from the anti-fraud service.
        3. Caches the result if the service provides a 'cache_until' value.
        """
        cache_key = f'antifraud_verdict_{user_email}'

        if cached_verdict := django.core.cache.cache.get(cache_key):
            return cached_verdict

        verdict = self._fetch_from_service(user_email, promo_id)

        if verdict.get('ok'):
            timeout_seconds = self._calculate_cache_timeout(
                verdict.get('cache_until'),
            )
            if timeout_seconds:
                django.core.cache.cache.set(
                    cache_key,
                    verdict,
                    timeout=timeout_seconds,
                )

        return verdict

    def _fetch_from_service(
        self,
        user_email: str,
        promo_id: str,
    ) -> typing.Dict:
        """
        Performs the actual HTTP request with a retry mechanism.
        """
        payload = {'user_email': user_email, 'promo_id': promo_id}

        for _ in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except (
                requests.exceptions.RequestException,
                json.JSONDecodeError,
            ):
                continue

        return {'ok': False, 'error': 'Anti-fraud service unavailable'}

    @staticmethod
    def _calculate_cache_timeout(
        cache_until_str: typing.Optional[str],
    ) -> typing.Optional[int]:
        """
        Safely parses an ISO format date string
        and returns a cache TTL in seconds.
        """
        if not cache_until_str:
            return None

        try:
            naive_dt = datetime.datetime.fromisoformat(cache_until_str)
            aware_dt = naive_dt.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)

            timeout_seconds = (aware_dt - now).total_seconds()
            return int(timeout_seconds) if timeout_seconds > 0 else None
        except (ValueError, TypeError):
            return None


antifraud_service = AntiFraudService()
