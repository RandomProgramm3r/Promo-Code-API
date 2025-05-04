import rest_framework.status

import user.tests.auth.base


class TestUserProfile(user.tests.auth.base.BaseUserAuthTestCase):
    def setUp(self):
        super().setUp()
        signup_data = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator@apple.com',
            'password': 'WhoLivesInCalifornia2000!',
            'other': {'age': 23, 'country': 'us'},
        }
        response = self.client.post(
            self.signup_url,
            signup_data,
            format='json',
        )
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        self.initial_token = token

    def test_get_profile_initial(self):
        response = self.client.get(self.user_profile_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        expected = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator@apple.com',
            'other': {'age': 23, 'country': 'us'},
        }
        self.assertEqual(response.json(), expected)

    def test_patch_profile_update_name_and_surname(self):
        payload = {'name': 'John', 'surname': 'Tsal'}
        response = self.client.patch(
            self.user_profile_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data.get('name'), 'John')
        self.assertEqual(response.data.get('surname'), 'Tsal')

    def test_patch_profile_update_avatar_url(self):
        payload = {'avatar_url': 'http://nodomain.com/kitten.jpeg'}
        response = self.client.patch(
            self.user_profile_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data.get('avatar_url'),
            'http://nodomain.com/kitten.jpeg',
        )

    def test_patch_password_and_check_persistence(self):
        new_password = 'MegaGiant88888@dooRuveS'
        self.client.patch(
            self.user_profile_url,
            {'name': 'John', 'surname': 'Tsal'},
            format='json',
        )
        self.client.patch(
            self.user_profile_url,
            {'avatar_url': 'http://nodomain.com/kitten.jpeg'},
            format='json',
        )
        response = self.client.patch(
            self.user_profile_url,
            {'password': new_password},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        data = response.data
        self.assertEqual(data.get('name'), 'John')
        self.assertEqual(data.get('surname'), 'Tsal')
        self.assertEqual(data.get('email'), 'creator@apple.com')
        self.assertEqual(data.get('other'), {'age': 23, 'country': 'us'})
        self.assertEqual(
            data.get('avatar_url'),
            'http://nodomain.com/kitten.jpeg',
        )

        # test old token still valid
        response = self.client.get(self.user_profile_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

    def test_auth_sign_in_old_password_fails(self):
        new_password = 'MegaGiant88888@dooRuveS'
        response = self.client.patch(
            self.user_profile_url,
            {'password': new_password},
            format='json',
        )
        self.client.credentials()
        response = self.client.post(
            self.signin_url,
            {
                'email': 'creator@apple.com',
                'password': 'WhoLivesInCalifornia2000!',
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_401_UNAUTHORIZED,
        )

    def test_auth_sign_in_new_password_succeeds(self):
        new_password = 'MegaGiant88888@dooRuveS'
        response = self.client.patch(
            self.user_profile_url,
            {'password': new_password},
            format='json',
        )
        self.client.credentials()
        response = self.client.post(
            self.signin_url,
            {
                'email': 'creator@apple.com',
                'password': 'MegaGiant88888@dooRuveS',
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
