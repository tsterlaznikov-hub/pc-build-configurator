from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.component_detail, name='component_detail'),
    path('catalog/<int:component_pk>/add-to-build/', views.add_to_build, name='add_to_build'),
    path('builds/', views.my_builds, name='my_builds'),
    path('builds/create/', views.build_create, name='build_create'),
    path('builds/<int:pk>/', views.build_detail, name='build_detail'),
    path('builds/<int:pk>/edit/', views.build_edit, name='build_edit'),
    path('builds/<int:pk>/delete/', views.build_delete, name='build_delete'),
    path('builds/<int:build_pk>/remove/<int:component_pk>/', views.remove_from_build, name='remove_from_build'),
    path('analytics/', views.analytics, name='analytics'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='configurator/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
]