import http

import django.test
import django.urls


class StaticURLTests(django.test.TestCase):
    def test_ping_endpoint(self):
        response = self.client.get(django.urls.reverse('core:ping'))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
