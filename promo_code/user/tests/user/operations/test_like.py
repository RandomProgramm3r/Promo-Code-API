import rest_framework.status
import rest_framework.test

import user.tests.user.base


class TestUserPromoLikeActions(user.tests.user.base.BaseUserTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user1_payload = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator1@apple.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        resp_user1 = cls.client.post(
            cls.user_signup_url,
            user1_payload,
            format='json',
        )
        assert resp_user1.status_code == rest_framework.status.HTTP_200_OK, (
            'User1 signup failed'
        )
        cls.user1_token = resp_user1.data['access']

        user2_payload = {
            'name': 'Mike',
            'surname': 'Bloomberg',
            'email': 'mike@bloomberg.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 15, 'country': 'us'},
        }
        resp_user2 = cls.client.post(
            cls.user_signup_url,
            user2_payload,
            format='json',
        )
        assert resp_user2.status_code == rest_framework.status.HTTP_200_OK, (
            'User2 signup failed'
        )
        cls.user2_token = resp_user2.data['access']

        user3_payload = {
            'name': 'Yefim',
            'surname': 'Dinitz',
            'email': 'algo@prog.lu',
            'password': 'HardPASSword1!',
            'other': {'age': 40, 'country': 'lu'},
        }
        resp_user3 = cls.client.post(
            cls.user_signup_url,
            user3_payload,
            format='json',
        )
        assert resp_user3.status_code == rest_framework.status.HTTP_200_OK, (
            'User3 signup failed'
        )
        cls.user3_token = resp_user3.data['access']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company1_token,
        )
        promo1_data = {
            'description': 'Active COMMON promo for all users',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp_promo1 = cls.client.post(
            cls.promo_list_create_url,
            promo1_data,
            format='json',
        )
        assert (
            resp_promo1.status_code == rest_framework.status.HTTP_201_CREATED
        ), f'Promo1 creation failed: {resp_promo1.data}'
        cls.promo1_id = resp_promo1.data['id']
        cls.client.credentials()

    def test_01_get_promo1_by_user1_initial_state(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo_id'], self.promo1_id)
        self.assertEqual(response.data['like_count'], 0)
        self.assertEqual(response.data['is_liked_by_user'], False)
        self.client.credentials()

    def test_02_get_promo1_by_company1_initial_state(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.get(
            self.get_business_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo_id'], self.promo1_id)
        self.assertEqual(response.data['like_count'], 0)
        self.client.credentials()

    def test_03_user1_likes_promo1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_04_user1_likes_promo1_again_idempotency(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_user_promo_like_url(self.promo1_id)
        self.client.post(url, format='json')

        response = self.client.post(url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_05_get_promo1_by_user1_after_like(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        like_response = self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            like_response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['promo_id'], self.promo1_id)
        self.assertEqual(response.data['like_count'], 1)
        self.assertEqual(response.data['is_liked_by_user'], True)
        self.client.credentials()

    def test_06_get_promo1_by_user2_before_own_like(self):
        original_user_client = rest_framework.test.APIClient()
        original_user_client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        original_user_client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 1)
        self.assertEqual(
            response.data['is_liked_by_user'],
            False,
        )
        self.client.credentials()

    def test_07_user2_likes_promo1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        response = self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_08_get_promo1_by_user2_after_own_like(self):
        temp_client_user1 = rest_framework.test.APIClient()
        temp_client_user1.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        temp_client_user1.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        like_response = self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            like_response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['like_count'],
            2,
        )
        self.assertEqual(response.data['is_liked_by_user'], True)
        self.client.credentials()

    def test_09_user3_deletes_non_existent_like_for_promo1_idempotency(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_10_get_promo1_by_user3_no_like_state(self):
        temp_client_user1 = rest_framework.test.APIClient()
        temp_client_user1.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        temp_client_user1.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        temp_client_user2 = rest_framework.test.APIClient()
        temp_client_user2.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        temp_client_user2.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['like_count'],
            2,
        )
        self.assertEqual(response.data['is_liked_by_user'], False)
        self.client.credentials()

    def test_11_get_promo1_by_company1_after_all_likes(self):
        temp_client_user1 = rest_framework.test.APIClient()
        temp_client_user1.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        temp_client_user1.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        temp_client_user2 = rest_framework.test.APIClient()
        temp_client_user2.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        temp_client_user2.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        response = self.client.get(
            self.get_business_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 2)
        self.client.credentials()

    def test_12_user1_unlikes_promo1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        response = self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_13_get_promo1_by_user1_after_unlike(self):
        temp_client_user2 = rest_framework.test.APIClient()
        temp_client_user2.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        temp_client_user2.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )

        self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['like_count'],
            1,
        )
        self.assertEqual(
            response.data['is_liked_by_user'],
            False,
        )
        self.client.credentials()

    def test_14_user1_unlikes_promo1_again_idempotency(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        self.client.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        response = self.client.delete(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data, {'status': 'ok'})
        self.client.credentials()

    def test_15_get_promo1_by_user1_final_state(self):
        temp_client_user2 = rest_framework.test.APIClient()
        temp_client_user2.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        temp_client_user2.post(
            self.get_user_promo_like_url(self.promo1_id),
            format='json',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )

        response = self.client.get(
            self.get_user_promo_detail_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(response.data['like_count'], 1)
        self.assertEqual(response.data['is_liked_by_user'], False)
        self.client.credentials()
