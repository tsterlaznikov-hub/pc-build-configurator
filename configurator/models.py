from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Component(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name='Категория'
    )
    brand = models.CharField(max_length=100, verbose_name='Производитель')
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена (USD)'
    )
    specs = models.JSONField(default=dict, verbose_name='Характеристики')
    image = models.ImageField(
        upload_to='components/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Комплектующее'
        verbose_name_plural = 'Комплектующие'
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.brand} {self.name}'


class Build(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название сборки')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='builds',
        verbose_name='Пользователь'
    )
    components = models.ManyToManyField(
        Component,
        blank=True,
        related_name='builds',
        verbose_name='Комплектующие'
    )
    is_public = models.BooleanField(default=False, verbose_name='Публичная')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Сборка'
        verbose_name_plural = 'Сборки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.username})'

    @property
    def total_price_usd(self) -> float:
        """Возвращает общую стоимость сборки в USD."""
        return sum(component.price_usd for component in self.components.all())

    @property
    def total_price_rub(self) -> float:
        """Возвращает общую стоимость сборки в рублях по актуальному курсу."""
        from configurator.services import get_usd_to_rub_rate
        rate = get_usd_to_rub_rate()
        return round(float(self.total_price_usd) * rate, 2)


class CompatibilityRule(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название правила')
    category_a = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='rules_as_a',
        verbose_name='Категория A'
    )
    category_b = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='rules_as_b',
        verbose_name='Категория B'
    )
    spec_key = models.CharField(
        max_length=100,
        verbose_name='Ключ характеристики',
        help_text='Например: socket, form_factor'
    )
    description = models.TextField(verbose_name='Описание правила')

    class Meta:
        verbose_name = 'Правило совместимости'
        verbose_name_plural = 'Правила совместимости'

    def __str__(self):
        return self.name