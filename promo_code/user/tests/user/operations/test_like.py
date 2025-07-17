import rest_framework.status

import user.tests.user.base


class TestUserPromoLikeActions(user.tests.user.base.BaseUserTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user1_token = cls._create_user_and_get_token(
            name='Steve',
            surname='Wozniak',
            email='creator1@apple.com',
            password='WhoLiveSInCalifornia2000!',
            other={'age': 60, 'country': 'gb'},
        )
        cls.user2_token = cls._create_user_and_get_token(
            name='Mike',
            surname='Bloomberg',
            email='mike@bloomberg.com',
            password='WhoLiveSInCalifornia2000!',
            other={'age': 15, 'country': 'us'},
        )
        cls.user3_token = cls._create_user_and_get_token(
            name='Yefim',
            surname='Dinitz',
            email='algo@prog.lu',
            password='HardPASSword1!',
            other={'age': 40, 'country': 'lu'},
        )

        cls.promo1_id = cls._create_promo(
            description='Active COMMON promo for all users',
            target={},
            max_count=10,
            active_from='2025-01-10',
            mode='COMMON',
            promo_common='sale-10',
        )

    @classmethod
    def _create_user_and_get_token(cls, name, surname, email, password, other):
        payload = {
            'name': name,
            'surname': surname,
            'email': email,
            'password': password,
            'other': other,
        }
        response = cls.client.post(cls.user_signup_url, payload, format='json')
        assert response.status_code == rest_framework.status.HTTP_200_OK
        return response.data['access']

    @classmethod
    def _create_promo(
        cls,
        description,
        target,
        max_count,
        active_from,
        mode,
        promo_common,
    ):
        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company1_token,
        )
        data = {
            'description': description,
            'target': target,
            'max_count': max_count,
            'active_from': active_from,
            'mode': mode,
            'promo_common': promo_common,
        }
        response = cls.client.post(
            cls.promo_list_create_url,
            data,
            format='json',
        )
        assert response.status_code == rest_framework.status.HTTP_201_CREATED
        cls.client.credentials()
        return response.data['id']

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def _get_user_promo(self, user_token):
        self._auth(user_token)
        return self.client.get(self.get_user_promo_detail_url(self.promo1_id))

    def _get_business_promo(self):
        self._auth(self.company1_token)
        return self.client.get(
            self.get_business_promo_detail_url(self.promo1_id),
        )

    def _like(self, token):
        self._auth(token)
        return self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

    def _unlike(self, token):
        self._auth(token)
        return self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

    def tearDown(self):
        super().tearDown()

        self.client.credentials()

    def test_initial_promo_state(self):
        response = self._get_user_promo(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 0)
        self.assertFalse(response.data['is_liked_by_user'])

        response = self._get_business_promo()
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 0)

    def test_like_action(self):
        response = self._like(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})

    def test_like_idempotency(self):
        self._like(self.user1_token)
        before = self._get_user_promo(self.user1_token)
        self.assertEqual(before.data['like_count'], 1)

        response = self._like(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        after = self._get_user_promo(self.user1_token)
        self.assertEqual(after.data['like_count'], 1)
        self.assertTrue(after.data['is_liked_by_user'])

    def test_unlike_action(self):
        self._like(self.user1_token)
        response = self._unlike(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        details = self._get_user_promo(self.user1_token)
        self.assertEqual(details.data['like_count'], 0)
        self.assertFalse(details.data['is_liked_by_user'])

    def test_unlike_idempotency(self):
        self._like(self.user1_token)
        self._unlike(self.user1_token)
        before = self._get_user_promo(self.user1_token)
        self.assertEqual(before.data['like_count'], 0)

        response = self._unlike(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        after = self._get_user_promo(self.user1_token)
        self.assertEqual(after.data['like_count'], 0)

    def test_unlike_nonexistent(self):
        response = self._unlike(self.user3_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

    def test_user1_state_after_user2_like_and_unlike(self):
        self._like(self.user2_token)
        self._like(self.user1_token)
        self._unlike(self.user1_token)

        response = self._get_user_promo(self.user1_token)
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 1)
        self.assertFalse(response.data['is_liked_by_user'])

    def test_multiple_user_likes(self):
        self._like(self.user1_token)

        user2_before = self._get_user_promo(self.user2_token)
        self.assertEqual(user2_before.data['like_count'], 1)
        self.assertFalse(user2_before.data['is_liked_by_user'])

        self._like(self.user2_token)
        user2_after = self._get_user_promo(self.user2_token)
        self.assertEqual(user2_after.data['like_count'], 2)
        self.assertTrue(user2_after.data['is_liked_by_user'])

        user3_response = self._get_user_promo(self.user3_token)
        self.assertEqual(user3_response.data['like_count'], 2)
        self.assertFalse(user3_response.data['is_liked_by_user'])

        business = self._get_business_promo()
        self.assertEqual(business.data['like_count'], 2)
