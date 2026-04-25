from django.urls import path
from . import page_views

urlpatterns = [
    path('', page_views.house_list, name='page-house-list'),
    path('create/', page_views.house_create, name='page-house-create'),
    path('join/', page_views.house_join, name='page-house-join'),
    path('<uuid:pk>/', page_views.house_detail, name='page-house-detail'),
    path('<uuid:pk>/edit/', page_views.house_edit, name='page-house-edit'),
    path('<uuid:pk>/delete/', page_views.house_delete, name='page-house-delete'),
    path('<uuid:pk>/members/', page_views.house_members, name='page-house-members'),
    path('<uuid:pk>/members/invite/', page_views.house_member_invite, name='page-house-member-invite'),
    path('<uuid:pk>/members/<uuid:member_pk>/role/', page_views.house_member_update_role, name='page-house-member-update-role'),
    path('<uuid:pk>/members/<uuid:member_pk>/remove/', page_views.house_member_remove, name='page-house-member-remove'),
    path('<uuid:pk>/leave/', page_views.house_leave, name='page-house-leave'),
    path('<uuid:pk>/rooms/create/', page_views.create_room, name='create-room'),
    path('<uuid:pk>/rooms/<uuid:room_pk>/delete/', page_views.delete_room, name='delete-room'),
    path('<uuid:pk>/plugs/move/', page_views.move_plug, name='move-plug'),
]
