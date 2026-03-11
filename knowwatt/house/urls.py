from django.urls import path
from .views import (
    HouseListCreateView,
    HouseDetailView,
    HouseUserListView,
    HouseUserInviteView,
    HouseUserManageView,
)

urlpatterns = [
    # House endpoints
    path('', HouseListCreateView.as_view(), name='house-list-create'),
    path('<uuid:house_id>/', HouseDetailView.as_view(), name='house-detail'),
    
    # User management endpoints (per documentation)
    path('<uuid:house_id>/users/', HouseUserListView.as_view(), name='house-user-list'),
    path('<uuid:house_id>/users/invite/', HouseUserInviteView.as_view(), name='house-user-invite'),
    path('<uuid:house_id>/users/manage/', HouseUserManageView.as_view(), name='house-user-manage'),
]
