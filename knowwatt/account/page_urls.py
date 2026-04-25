from django.urls import path
from . import page_views

urlpatterns = [
    path('', page_views.profile_view, name='page-profile'),
    path('edit/', page_views.profile_edit, name='page-profile-edit'),
    path('password/', page_views.password_change, name='page-password-change'),
]
