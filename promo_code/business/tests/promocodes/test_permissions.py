import django.contrib.auth
import rest_framework.status
import rest_framework.test

import business.models
import business.permissions
import business.tests.promocodes.base
import user.models


class TestIsCompanyUserPermission(
    business.tests.promocodes.base.BasePromoTestCase,
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.unique_payload = {
            'description': 'Complimentary Pudge Skin on Registration!',
            'target': {},
            'max_count': 1,
            'mode': 'UNIQUE',
            'active_from': '2030-08-08',
            'promo_unique': ['dota-arena', 'coda-core', 'warcraft3'],
        }

    def setUp(self):
        self.factory = rest_framework.test.APIRequestFactory()
        self.permission = business.permissions.IsCompanyUser()
        get_user_model = django.contrib.auth.get_user_model
        self.regular_user = get_user_model().objects.create_user(
            name='regular',
            password='SecurePass123!',
            surname='adadioa',
            email='example@gmail.com',
        )

    def create_promo(self, token, payload):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        response = self.client.post(
            self.promo_create_url,
            payload,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_201_CREATED,
        )
        return response.data['id']

    def tearDown(self):
        business.models.Company.objects.all().delete()
        user.models.User.objects.all().delete()

    def test_has_permission_for_company_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = self.company1
        self.assertTrue(self.permission.has_permission(request, None))

    def test_has_permission_for_regular_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = self.regular_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_has_permission_for_anonymous_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = None
        self.assertFalse(self.permission.has_permission(request, None))

    def test_has_permission_to_foreign_promo(self):
        promo_id = self.create_promo(self.company2_token, self.unique_payload)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.company1_token,
        )
        url = self.promo_detail_url(promo_id)
        patch_payload = {'description': '100% Cashback'}
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(
            response.status_code,
            rest_framework.status.HTTP_403_FORBIDDEN,
        )
