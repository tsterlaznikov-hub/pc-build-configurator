from django.contrib import admin
from .models import Category, Component, Build, CompatibilityRule


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'price_usd', 'created_at']
    search_fields = ['name', 'brand']
    list_filter = ['category', 'brand']


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_public', 'created_at']
    search_fields = ['name', 'user__username']
    list_filter = ['is_public']


@admin.register(CompatibilityRule)
class CompatibilityRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_a', 'category_b', 'spec_key']
    search_fields = ['name']