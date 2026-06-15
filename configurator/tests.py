from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from .models import Category, Component, Build, CompatibilityRule
from .services import convert_to_rub, check_compatibility


class CategoryModelTest(TestCase):
    def test_category_str(self):
        category = Category.objects.create(name='CPU', slug='cpu')
        self.assertEqual(str(category), 'CPU')


class ComponentModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='CPU', slug='cpu')
        self.component = Component.objects.create(
            name='Core i5-13600K',
            category=self.category,
            brand='Intel',
            price_usd=319.99,
            specs={'socket': 'LGA1700'}
        )

    def test_component_str(self):
        self.assertEqual(str(self.component), 'Intel Core i5-13600K')

    def test_component_price(self):
        self.assertEqual(float(self.component.price_usd), 319.99)


class BuildModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.build = Build.objects.create(name='Тестовая сборка', user=self.user)

    def test_build_str(self):
        self.assertEqual(str(self.build), 'Тестовая сборка (testuser)')

    def test_build_total_price_empty(self):
        self.assertEqual(self.build.total_price_usd, 0)

    def test_build_total_price_with_components(self):
        category = Category.objects.create(name='CPU', slug='cpu')
        component = Component.objects.create(
            name='Core i5', category=category, brand='Intel', price_usd=300.00
        )
        self.build.components.add(component)
        self.assertEqual(float(self.build.total_price_usd), 300.00)


class ConvertToRubTest(TestCase):
    @patch('configurator.services.get_usd_to_rub_rate')
    def test_convert_to_rub(self, mock_rate):
        mock_rate.return_value = 90.0
        result = convert_to_rub(100)
        self.assertEqual(result, 9000.0)

    @patch('configurator.services.get_usd_to_rub_rate')
    def test_convert_zero(self, mock_rate):
        mock_rate.return_value = 90.0
        result = convert_to_rub(0)
        self.assertEqual(result, 0.0)


class CompatibilityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.cpu_cat = Category.objects.create(name='CPU', slug='cpu')
        self.mb_cat = Category.objects.create(name='Motherboard', slug='motherboard')
        self.cpu = Component.objects.create(
            name='Core i5', category=self.cpu_cat, brand='Intel',
            price_usd=300, specs={'socket': 'LGA1700'}
        )
        self.mb_compatible = Component.objects.create(
            name='Z790', category=self.mb_cat, brand='Gigabyte',
            price_usd=300, specs={'socket': 'LGA1700'}
        )
        self.mb_incompatible = Component.objects.create(
            name='X670', category=self.mb_cat, brand='ASRock',
            price_usd=300, specs={'socket': 'AM5'}
        )
        self.rule = CompatibilityRule.objects.create(
            name='Совместимость сокета',
            category_a=self.cpu_cat,
            category_b=self.mb_cat,
            spec_key='socket',
            description='Сокеты должны совпадать'
        )

    def test_compatible_components(self):
        build = Build.objects.create(name='Хорошая сборка', user=self.user)
        build.components.add(self.cpu, self.mb_compatible)
        warnings = check_compatibility(build)
        self.assertEqual(len(warnings), 0)

    def test_incompatible_components(self):
        build = Build.objects.create(name='Плохая сборка', user=self.user)
        build.components.add(self.cpu, self.mb_incompatible)
        warnings = check_compatibility(build)
        self.assertEqual(len(warnings), 1)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_catalog_page(self):
        response = self.client.get('/catalog/')
        self.assertEqual(response.status_code, 200)

    def test_my_builds_requires_login(self):
        response = self.client.get('/builds/')
        self.assertEqual(response.status_code, 302)

    def test_my_builds_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/builds/')
        self.assertEqual(response.status_code, 200)