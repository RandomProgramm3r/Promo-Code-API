import parameterized
import rest_framework.status

import user.tests.user.base


class ProfileAPITestCase(user.tests.user.base.BaseUserTestCase):
    def setUp(self):
        super().setUp()
        signup_data = {
            'name': 'Jack',
            'surname': 'Sparrow',
            'email': 'sparrow@movie.com',
            'password': 'WhoLivesInTheOcean100500!',
            'other': {'age': 48, 'country': 'gb'},
        }
        response = self.client.post(
            self.user_signup_url,
            signup_data,
            format='json',
        )
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_update_profile_empty_name_and_surname(self):
        payload = {'name': '', 'surname': ''}
        response = self.client.patch(
            self.user_profile_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('no_scheme', 'notURLcom'),
            ('only_scheme', 'https://'),
            ('no_domain', 'https://.com'),
        ],
    )
    def test_update_profile_invalid_avatar_url(self, _, url):
        payload = {'avatar_url': url}
        response = self.client.patch(
            self.user_profile_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    @parameterized.parameterized.expand(
        [
            ('simple_alpha_num', 'pro100'),
            ('only_symbols', '!!!!!'),
            ('only_nums', '1234567890'),
            ('only_lowercase_chars', 'abcdefghijklmno'),
            ('only_uppercase-chars', 'ABCDEFGHIJKLMNO'),
            ('only_symbols_and_nums', '1234567890!@#$%^&*()_+{}|:"<>?'),
            ('repetitive_chars', 'onlyYOUOOOO!'),
            ('mixed_short', 'yOu!@1'),
            ('repeating_pattern', '11111@@@@@aaaaa'),
        ],
    )
    def test_update_profile_weak_password(self, _, pwd):
        payload = {'password': pwd}
        response = self.client.patch(
            self.user_profile_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_400_BAD_REQUEST,
        )

    def test_get_profile(self):
        response = self.client.get(self.user_profile_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected = {
            'name': 'Jack',
            'surname': 'Sparrow',
            'email': 'sparrow@movie.com',
            'other': {'age': 48, 'country': 'gb'},
        }
        self.assertEqual(response.json(), expected)
