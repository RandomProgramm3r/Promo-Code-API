import django.contrib.auth
import rest_framework.status
import rest_framework.test

import business.models
import business.permissions
import business.tests.promocodes.base
import user.models


class TestIsCompanyUserPermission(
    business.tests.promocodes.base.BasePromoCreateTestCase,
):
    def setUp(self):
        self.factory = rest_framework.test.APIRequestFactory()
        self.permission = business.permissions.IsCompanyUser()
        get_user_model = django.contrib.auth.get_user_model
        self.regular_user = get_user_model().objects.create_user(
            name='regular',
            password='testpass123',
            surname='adadioa',
            email='example@gmail.com',
        )
        self.company_user = business.models.Company.objects.create_company(
            password='testpass123',
            name='Test Company',
            email='exampl3e@gmail.com',
        )

    def tearDown(self):
        business.models.Company.objects.all().delete()
        user.models.User.objects.all().delete()

    def test_has_permission_for_company_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = self.company_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_has_permission_for_regular_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = self.regular_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_has_permission_for_anonymous_user(self):
        request = self.factory.get(self.promo_create_url)
        request.user = None
        self.assertFalse(self.permission.has_permission(request, None))
