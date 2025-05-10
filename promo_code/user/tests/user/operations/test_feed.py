import datetime

import rest_framework.status

import user.tests.user.base


class TestUserPromoFeed(user.tests.user.base.BaseUserTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        user1_payload = {
            'name': 'Steve',
            'surname': 'Wozniak',
            'email': 'creator1@apple.com',
            'password': 'WhoLiveSInCalifornia2000!',
            'other': {'age': 60, 'country': 'gb'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user1_payload,
            format='json',
        )

        cls.user1_token = resp.data['access']

        user2_payload = {
            'name': 'Mike',
            'surname': 'Bloomberg',
            'email': 'mike@bloomberg.com',
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
            'email': 'algo@prog.ru',
            'password': 'HardPASSword1!',
            'other': {'age': 40, 'country': 'LU'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user3_payload,
            format='json',
        )

        cls.user3_token = resp.data['access']

        user4_payload = {
            'name': 'Leslie',
            'surname': 'Lamport',
            'email': 'leslie@lamport.com',
            'password': 'Everyth1ngIsDistributed!',
            'other': {'age': 80, 'country': 'sg'},
        }
        resp = cls.client.post(
            cls.user_signup_url,
            user4_payload,
            format='json',
        )

        cls.user4_token = resp.data['access']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company1_token,
        )

        today = datetime.date.today()

        promo1 = {
            'description': 'Active COMMON promo, no target',
            'target': {},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo1,
            format='json',
        )

        cls.promo1_id = resp.data['id']

        promo2 = {
            'description': 'Active COMMON promo for fr',
            'target': {
                'country': 'fr',
                'categories': ['ios', 'tbank', 'CATS'],
            },
            'max_count': 6,
            'active_from': '2023-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo2,
            format='json',
        )

        cls.promo2_id = resp.data['id']

        promo3 = {
            'description': 'Inactive COMMON promo for us, age 13+',
            'target': {'country': 'us', 'age_from': 13, 'categories': ['ios']},
            'max_count': 100000,
            'active_until': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-30',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo3,
            format='json',
        )
        cls.promo3_id = resp.data['id']

        promo4 = {
            'description': 'Active UNIQUE promo for lu, age 20-60',
            'target': {
                'country': 'lu',
                'age_from': 20,
                'age_until': 60,
                'categories': ['television'],
            },
            'max_count': 1,
            'active_from': (today - datetime.timedelta(days=1)).strftime(
                '%Y-%m-%d',
            ),
            'active_until': '2055-01-10',
            'mode': 'UNIQUE',
            'promo_unique': ['dream', 'of:', 'californication'],
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo4,
            format='json',
        )
        cls.promo4_id = resp.data['id']

        promo5 = {
            'description': 'Active COMMON promo for lu, age up to 50',
            'target': {'country': 'lu', 'age_until': 50},
            'max_count': 1000,
            'active_from': '2023-01-10',
            'active_until': '2080-05-30',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo5,
            format='json',
        )
        cls.promo5_id = resp.data['id']

        cls.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + cls.company2_token,
        )

        promo6 = {
            'description': 'Inactive COMMON promo for fr, age 5-90',
            'target': {
                'country': 'fr',
                'age_from': 5,
                'age_until': 90,
                'categories': ['Television'],
            },
            'max_count': 1,
            'active_from': '2040-12-08',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo6,
            format='json',
        )
        cls.promo6_id = resp.data['id']

        promo7 = {
            'description': 'Active COMMON promo for lu, age 16+',
            'target': {
                'country': 'lu',
                'age_from': 16,
                'categories': ['Television'],
            },
            'max_count': 1,
            'active_from': (today - datetime.timedelta(days=1)).strftime(
                '%Y-%m-%d',
            ),
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo7,
            format='json',
        )
        cls.promo7_id = resp.data['id']

        promo8 = {
            'description': 'Inactive COMMON promo for all, max_count 0',
            'target': {'categories': ['TELEVISION']},
            'max_count': 0,
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo8,
            format='json',
        )
        cls.promo8_id = resp.data['id']

        promo9 = {
            'description': 'Active COMMON promo for lu, age up to 70',
            'target': {'country': 'lu', 'age_until': 70},
            'max_count': 1,
            'active_from': (today - datetime.timedelta(days=1)).strftime(
                '%Y-%m-%d',
            ),
            'active_until': '2099-08-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo9,
            format='json',
        )
        cls.promo9_id = resp.data['id']

        promo10 = {
            'description': 'Active COMMON promo for KZ',
            'target': {'country': 'kz'},
            'max_count': 10,
            'active_from': '2025-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo10,
            format='json',
        )
        cls.promo10_id = resp.data['id']

        promo11 = {
            'description': 'Active COMMON promo for SG',
            'target': {'country': 'sg'},
            'max_count': 1000,
            'active_from': '2023-01-10',
            'mode': 'COMMON',
            'promo_common': 'sale-10',
        }
        resp = cls.client.post(
            cls.promo_list_create_url,
            promo11,
            format='json',
        )
        cls.promo11_id = resp.data['id']

        cls.client.credentials()

    def test_user1_gb_60_get_all_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user1_token,
        )
        response = self.client.get(self.user_feed_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '2')

        expected_data = [
            {
                'promo_id': self.promo8_id,
                'company_name': self.company2_name,
                'active': False,
            },
            {
                'promo_id': self.promo1_id,
                'company_name': self.company1_name,
                'active': True,
            },
        ]
        actual_data = [
            {
                'promo_id': item['promo_id'],
                'company_name': item['company_name'],
                'active': item['active'],
            }
            for item in response.data
        ]
        self.assertEqual(actual_data, expected_data)

    def test_user2_us_15_get_all_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user2_token,
        )
        response = self.client.get(self.user_feed_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '3')

        expected_data = [
            {
                'promo_id': self.promo8_id,
                'company_name': self.company2_name,
                'active': False,
            },
            {
                'promo_id': self.promo3_id,
                'company_name': self.company1_name,
                'active': False,
            },
            {
                'promo_id': self.promo1_id,
                'company_name': self.company1_name,
                'active': True,
            },
        ]
        actual_data = [
            {
                'promo_id': item['promo_id'],
                'company_name': item['company_name'],
                'active': item['active'],
            }
            for item in response.data
        ]
        self.assertEqual(actual_data, expected_data)

    def test_user3_lu_40_get_all_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(self.user_feed_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '6')

        expected_data = [
            {
                'promo_id': self.promo9_id,
                'company_name': self.company2_name,
                'active': True,
            },
            {
                'promo_id': self.promo8_id,
                'company_name': self.company2_name,
                'active': False,
            },
            {
                'promo_id': self.promo7_id,
                'company_name': self.company2_name,
                'active': True,
            },
            {
                'promo_id': self.promo5_id,
                'company_name': self.company1_name,
                'active': True,
            },
            {
                'promo_id': self.promo4_id,
                'company_name': self.company1_name,
                'active': True,
            },
            {
                'promo_id': self.promo1_id,
                'company_name': self.company1_name,
                'active': True,
            },
        ]
        actual_data = [
            {
                'promo_id': item['promo_id'],
                'company_name': item['company_name'],
                'active': item['active'],
            }
            for item in response.data
        ]
        self.assertEqual(actual_data, expected_data)

    def test_user3_lu_40_get_all_promos_pagination_offset2_limit3(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'offset': 2, 'limit': 3},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '6')

        expected_ids = [self.promo7_id, self.promo5_id, self.promo4_id]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertEqual(actual_ids, expected_ids)

    def test_user3_lu_40_get_all_promos_pagination_offset10_limit2(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'offset': 10, 'limit': 2},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '6')
        self.assertEqual(response.data, [])

    def test_user3_lu_40_get_all_promos_pagination_offset3_limit1(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'offset': 3, 'limit': 1},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '6')

        expected_ids = [self.promo5_id]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertEqual(actual_ids, expected_ids)

    def test_user3_lu_40_get_active_true_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'active': 'true'},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '5')

        expected_ids = [
            self.promo9_id,
            self.promo7_id,
            self.promo5_id,
            self.promo4_id,
            self.promo1_id,
        ]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertCountEqual(
            actual_ids,
            expected_ids,
        )

    def test_user3_lu_40_get_active_true_promos_pagination_offset2_limit2(
        self,
    ):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'active': 'true', 'limit': 2, 'offset': 2},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '5')

        expected_ids = [self.promo5_id, self.promo4_id]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertEqual(
            actual_ids,
            expected_ids,
        )

    def test_user3_lu_40_get_active_false_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'active': 'false'},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '1')

        expected_ids = [self.promo8_id]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertEqual(actual_ids, expected_ids)

    def test_user3_lu_40_get_promos_by_category_television_mixed_case_query(
        self,
    ):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'category': 'televiSION'},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '3')

        expected_ids = [
            self.promo8_id,
            self.promo7_id,
            self.promo4_id,
        ]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertCountEqual(
            actual_ids,
            expected_ids,
        )

    def test_user3_lu_40_get_active_true_promos_by_category_television(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'category': 'television', 'active': 'true'},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '2')

        expected_ids = [
            self.promo7_id,
            self.promo4_id,
        ]
        actual_ids = [item['promo_id'] for item in response.data]
        self.assertCountEqual(actual_ids, expected_ids)

    def test_user3_lu_40_get_promos_by_non_existent_category(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user3_token,
        )
        response = self.client.get(
            self.user_feed_url,
            {'category': 'non-exist-category'},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response['X-Total-Count'], '0')
        self.assertEqual(response.data, [])

    def test_user4_sg_80_get_all_promos(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user4_token,
        )
        response = self.client.get(self.user_feed_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response.headers['X-Total-Count'], '3')

        data = response.data
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['promo_id'], self.promo11_id)
        self.assertTrue(data[0]['active'])
        self.assertEqual(data[1]['promo_id'], self.promo8_id)
        self.assertEqual(data[2]['promo_id'], self.promo1_id)

    def test_user4_sg_80_get_all_promos_after_edit(self):
        # WARNING: this test globally changes the 'active' status of promo11
        # for all subsequent tests

        # Company edits promo11 to inactive
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company2_token,
        )
        url = self.get_promo_business_detail_url(self.promo11_id)
        patch_data = {'active_until': '2024-08-10'}
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.user4_token,
        )
        response = self.client.get(self.user_feed_url, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_200_OK,
        )
        for item in response.data:
            self.assertNotIn('promo_common', item)
            self.assertNotIn('promo_unique', item)
        self.assertEqual(response.headers['X-Total-Count'], '3')

        data = response.data
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['promo_id'], self.promo11_id)
        self.assertFalse(data[0]['active'])
        self.assertEqual(data[1]['promo_id'], self.promo8_id)
        self.assertEqual(data[2]['promo_id'], self.promo1_id)
