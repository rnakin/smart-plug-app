from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('home/', views.home_page, name='page-home'),
]
