import django.urls
import parameterized
import rest_framework.status

import user.tests.user.base


class PromoCommentsTestCase(user.tests.user.base.BaseUserTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def get_comment_list_url(promo_id):
            return django.urls.reverse(
                'api-user:user-promo-comment-list-create',
                kwargs={'promo_id': promo_id},
            )

        def get_comment_detail_url(promo_id, comment_id):
            return django.urls.reverse(
                'api-user:user-promo-comment-detail',
                kwargs={'promo_id': promo_id, 'comment_id': comment_id},
            )

        cls.get_comment_list_url = staticmethod(get_comment_list_url)
        cls.get_comment_detail_url = staticmethod(get_comment_detail_url)

        user1_payload = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator2@apple.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user1_payload,
            format='json',
        )
        cls.user1_token = resp.data['access']
        cls.user1_name = user1_payload['name']
        cls.user1_surname = user1_payload['surname']

        user2_payload = {
            'name': 'Mike',
            'surname': 'Bloomberg',
            'email': 'mike2@bloomberg.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 15, 'country': 'us'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user2_payload,
            format='json',
        )
        cls.user2_token = resp.data['access']

        user3_payload = {
            'name': 'Yefim',
            'surname': 'Dinitz',
            'email': 'algo3@prog.ru',
            'password': 'HardPASSword1!',
            'other': {'age': 40, 'country': 'kz'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user3_payload,
            format='json',
        )
        cls.user3_token = resp.data['access']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company1_token,
        )
        promo1_payload = {
            'description': '[1] Active COMMON promo code for all',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo1_payload,
            format='json',
        )
        cls.promo1_id = resp.data['id']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company2_token,
        )
        promo2_payload = {
            'description': '[2] Active COMMON promo code for kz, age from 28',
            'target': {
                'country': 'kz',
                'age_from': 28,
            },
            'max_count': 10,
            'active_from': '2025-02-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo2_payload,
            format='json',
        )
        cls.promo2_id = resp.data['id']

        cls.client.credentials()

    def _create_comment(self, token, promo_id, text):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        payload = {'text': text}
        url = self.get_comment_list_url(promo_id)
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(
            resp.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        return resp.data

    def _create_promo1_comments(self):
        comment1 = self._create_comment(
            self.user1_token,
            self.promo1_id,
            '[1] Comment for promo1 from user1',
        )
        comment2 = self._create_comment(
            self.user1_token,
            self.promo1_id,
            '[2] Comment for promo1 from user1',
        )
        comment5 = self._create_comment(
            self.user3_token,
            self.promo1_id,
            '[5] Comment for promo1 from user3',
        )
        return comment1['id'], comment2['id'], comment5['id']

    def _create_promo2_comments(self):
        comment3 = self._create_comment(
            self.user2_token,
            self.promo2_id,
            '[3] Comment for promo2 from user2',
        )
        comment4 = self._create_comment(
            self.user2_token,
            self.promo2_id,
            '[4] Comment for promo2 from user2',
        )
        return comment3['id'], comment4['id']

    def test_retrieve_promo1_initial_comment_count(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_user_promo_detail_url(self.promo1_id)
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('promo_id'), self.promo1_id)
        self.assertEqual(resp.data.get('comment_count'), 0)

    def test_add_comment_to_promo1_user1_first(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_list_url(self.promo1_id)
        payload = {'text': '[1] Comment for promo1 from user1'}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(
            resp.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        self.assertEqual(resp.data.get('text'), payload['text'])
        author = resp.data.get('author', {})
        self.assertEqual(author.get('name'), self.user1_name)
        self.assertEqual(author.get('surname'), self.user1_surname)

    def test_retrieve_promo1_after_comments(self):
        self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_user_promo_detail_url(self.promo1_id)
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('promo_id'), self.promo1_id)
        self.assertEqual(resp.data.get('comment_count'), 3)

    def test_retrieve_promo2_after_comments(self):
        self._create_promo2_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        url = self.get_user_promo_detail_url(self.promo2_id)
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('promo_id'), self.promo2_id)
        self.assertEqual(resp.data.get('comment_count'), 2)

    def test_list_comments_on_promo1(self):
        comment1_id, comment2_id, comment5_id = self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_list_url(self.promo1_id)
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        returned_ids = [item.get('id') for item in resp.data]
        expected_order = [comment5_id, comment2_id, comment1_id]
        self.assertEqual(returned_ids, expected_order)

    def test_list_comments_on_promo1_with_pagination(self):
        comment1_id, comment2_id, comment5_id = self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_list_url(self.promo1_id)
        resp = self.client.get(url, {'limit': 5, 'offset': 1}, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        returned_ids = [item.get('id') for item in resp.data]
        expected_slice = [comment2_id, comment1_id]
        self.assertEqual(returned_ids, expected_slice)
        self.assertEqual(int(resp.headers.get('X-Total-Count')), 3)

    def test_get_comment_by_id_valid(self):
        comment_text = '[1] Comment for promo1 from user1'
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            comment_text,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment['id'])
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('text'), comment_text)

    @parameterized.parameterized.expand(
        [
            (
                'promo2_id',
                'user1_token',
                'promo1_id',
            ),
            (
                'promo1_id',
                'user2_token',
                'promo2_id',
            ),
        ],
    )
    def test_get_comment_by_id_invalid_promo_comment_pair(
        self,
        url_promo_key,
        owner_token_key,
        creation_promo_key,
    ):
        owner_token = getattr(self, owner_token_key)
        creation_promo_id = getattr(self, creation_promo_key)
        url_promo_id = getattr(self, url_promo_key)

        comment = self._create_comment(
            owner_token,
            creation_promo_id,
            'some cool text',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        url = self.get_comment_detail_url(url_promo_id, comment['id'])
        resp = self.client.get(url, format='json')
        self.assertEqual(
            resp.status_code,
            rest_framework.status.HTTP_404_NOT_FOUND,
        )

    def test_edit_comment1_success(self):
        original_text = '[1] Original comment for promo1 from user1'
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            original_text,
        )
        comment1_id = comment['id']
        comment1_date = comment['date']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment1_id)
        edited_text = '[1] Edited version of comment for promo1 from user1'
        payload = {'text': edited_text}

        resp = self.client.put(url, payload, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('id'), comment1_id)
        self.assertEqual(resp.data.get('text'), edited_text)
        self.assertEqual(resp.data.get('date'), comment1_date)

        get_resp = self.client.get(url, format='json')
        self.assertEqual(
            get_resp.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(get_resp.data.get('text'), edited_text)

    def test_edit_comment1_not_owner(self):
        original_text = 'This comment belongs to user1'
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            original_text,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment['id'])
        payload = {'text': 'This should not succeed!'}
        resp = self.client.put(url, payload, format='json')
        self.assertEqual(
            resp.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        get_resp = self.client.get(url, format='json')
        self.assertEqual(
            get_resp.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        self.assertEqual(get_resp.data.get('text'), original_text)

    def test_list_comments_on_promo1_after_edit(self):
        comment1_id, comment2_id, comment5_id = self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment1_id)
        payload = {'text': 'Edited text'}
        self.client.put(url, payload, format='json')

        resp = self.client.get(
            self.get_comment_list_url(self.promo1_id),
            format='json',
        )
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        returned_ids = [item.get('id') for item in resp.data]
        expected_order = [comment5_id, comment2_id, comment1_id]
        self.assertEqual(returned_ids, expected_order)

    @parameterized.parameterized.expand(
        [
            ('PUT', 'user3_token', rest_framework.status.HTTP_403_FORBIDDEN),
            (
                'DELETE',
                'user3_token',
                rest_framework.status.HTTP_403_FORBIDDEN,
            ),
            ('PUT', 'user1_token', rest_framework.status.HTTP_404_NOT_FOUND),
            (
                'DELETE',
                'user1_token',
                rest_framework.status.HTTP_404_NOT_FOUND,
            ),
        ],
    )
    def test_actions_on_comment_with_invalid_context(
        self,
        method,
        token_key,
        expected_status,
    ):
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            'some cool text',
        )

        if expected_status == rest_framework.status.HTTP_403_FORBIDDEN:
            url = self.get_comment_detail_url(self.promo1_id, comment['id'])
        else:
            url = self.get_comment_detail_url(self.promo2_id, comment['id'])

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + getattr(self, token_key),
        )

        if method == 'PUT':
            resp = self.client.put(
                url,
                {'text': 'new awesome text'},
                format='json',
            )
        else:
            resp = self.client.delete(url, format='json')

        self.assertEqual(resp.status_code, expected_status)

    def test_delete_comment1_success(self):
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            'A comment to be deleted',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment['id'])

        resp = self.client.delete(url, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('status'), 'ok')

        get_resp = self.client.get(url, format='json')
        self.assertEqual(
            get_resp.status_code,
            rest_framework.status.HTTP_404_NOT_FOUND,
        )

    def test_delete_comment1_not_found(self):
        comment = self._create_comment(
            self.user1_token,
            self.promo1_id,
            'A comment to be deleted twice',
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url = self.get_comment_detail_url(self.promo1_id, comment['id'])

        resp1 = self.client.delete(url, format='json')
        self.assertEqual(resp1.status_code, rest_framework.status.HTTP_200_OK)

        resp2 = self.client.delete(url, format='json')
        self.assertEqual(
            resp2.status_code,
            rest_framework.status.HTTP_404_NOT_FOUND,
        )

    def test_retrieve_promo1_after_deletion(self):
        comment1_id, _, _ = self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url_to_delete = self.get_comment_detail_url(
            self.promo1_id,
            comment1_id,
        )
        resp = self.client.delete(url_to_delete, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('status'), 'ok')

        url_promo = self.get_user_promo_detail_url(self.promo1_id)
        resp = self.client.get(url_promo, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)
        self.assertEqual(resp.data.get('promo_id'), self.promo1_id)
        self.assertEqual(resp.data.get('comment_count'), 2)

    def test_list_comments_on_promo1_after_deletion(self):
        comment1_id, comment2_id, comment5_id = self._create_promo1_comments()

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        url_to_delete = self.get_comment_detail_url(
            self.promo1_id,
            comment1_id,
        )
        resp = self.client.delete(url_to_delete, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)

        url_list = self.get_comment_list_url(self.promo1_id)
        resp = self.client.get(url_list, format='json')
        self.assertEqual(resp.status_code, rest_framework.status.HTTP_200_OK)

        returned_ids = [item.get('id') for item in resp.data]
        expected_remaining = [comment5_id, comment2_id]
        self.assertEqual(returned_ids, expected_remaining)
        self.assertEqual(int(resp.headers.get('X-Total-Count')), 2)
