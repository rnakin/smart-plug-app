  
from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('verify-email/', views.verify_email_page),
    path('forgot-password/', views.forgot_password_page),
    path('reset-password/', views.reset_password_page),
]