import datetime
import unittest.mock

import django.test
import requests.exceptions

import user.antifraud_service


class AntiFraudServiceTests(django.test.SimpleTestCase):
    def setUp(self):
        self.service = user.antifraud_service.AntiFraudService()
        self.user_email = 'test@example.com'
        self.promo_id = '1bfd61b1-52ff-4c0f-ba8b-434ad3d0f812'

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_get_verdict_from_cache(self, mock_cache, mock_post):
        mock_cache.get.return_value = {'ok': True, 'reason': 'From Cache'}

        result = self.service.get_verdict(self.user_email, self.promo_id)

        mock_cache.get.assert_called_once_with(
            f'antifraud_verdict_{self.user_email}',
        )
        mock_post.assert_not_called()
        self.assertEqual(result, {'ok': True, 'reason': 'From Cache'})

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_fetch_from_service_and_set_cache(self, mock_cache, mock_post):
        mock_cache.get.return_value = None

        now = datetime.datetime.now(datetime.timezone.utc)
        api_data = {
            'ok': True,
            'cache_until': (now + datetime.timedelta(seconds=60)).isoformat(),
        }
        mock_response = unittest.mock.MagicMock(
            status_code=200,
            json=unittest.mock.MagicMock(return_value=api_data),
        )
        mock_post.return_value = mock_response

        result = self.service.get_verdict(self.user_email, self.promo_id)

        mock_cache.get.assert_called_once_with(
            f'antifraud_verdict_{self.user_email}',
        )
        mock_post.assert_called_once()
        mock_cache.set.assert_called_once()
        key, val = mock_cache.set.call_args[0][:2]
        timeout = mock_cache.set.call_args[1]['timeout']
        self.assertEqual(key, f'antifraud_verdict_{self.user_email}')
        self.assertEqual(val, api_data)
        self.assertAlmostEqual(timeout, 60, delta=1)
        self.assertEqual(result, api_data)

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_cache_is_not_set_if_verdict_is_not_ok(
        self,
        mock_cache,
        mock_post,
    ):
        mock_cache.get.return_value = None
        api_data = {'ok': False, 'reason': 'Blocked'}
        mock_response = unittest.mock.MagicMock(
            status_code=200,
            json=unittest.mock.MagicMock(return_value=api_data),
        )
        mock_post.return_value = mock_response

        result = self.service.get_verdict(self.user_email, self.promo_id)

        mock_post.assert_called_once()
        mock_cache.set.assert_not_called()
        self.assertEqual(result, api_data)

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_handles_antifraud_service_unavailable(
        self,
        mock_cache,
        mock_post,
    ):
        mock_cache.get.return_value = None
        mock_post.side_effect = requests.exceptions.RequestException(
            'Connection timed out',
        )

        result = self.service.get_verdict(self.user_email, self.promo_id)

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(
            result,
            {'ok': False, 'error': 'Anti-fraud service unavailable'},
        )

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_does_not_set_cache_with_invalid_date(self, mock_cache, mock_post):
        mock_cache.get.return_value = None
        api_data = {'ok': True, 'cache_until': 'invalid-date-format'}
        mock_response = unittest.mock.MagicMock(
            json=unittest.mock.MagicMock(return_value=api_data),
        )
        mock_post.return_value = mock_response

        self.service.get_verdict(self.user_email, self.promo_id)

        mock_cache.set.assert_not_called()

    @unittest.mock.patch('user.antifraud_service.requests.post')
    @unittest.mock.patch('user.antifraud_service.django.core.cache.cache')
    def test_handles_api_http_error(self, mock_cache, mock_post):
        mock_cache.get.return_value = None
        mock_response = unittest.mock.MagicMock(status_code=500)

        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError('Server Error')
        )
        mock_post.return_value = mock_response

        result = self.service.get_verdict(self.user_email, self.promo_id)

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(
            result,
            {'ok': False, 'error': 'Anti-fraud service unavailable'},
        )
