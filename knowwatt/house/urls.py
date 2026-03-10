from django.urls import path
from .views import (
    HouseListCreateView,
    HouseDetailView,
    HouseUserListView,
    HouseUserInviteView,
    HouseUserDetailView,
)

urlpatterns = [
    # House endpoints
    path('', HouseListCreateView.as_view(), name='house-list-create'),
    path('<uuid:house_id>/', HouseDetailView.as_view(), name='house-detail'),
    
    # User management endpoints (per documentation)
    path('<uuid:house_id>/users/', HouseUserListView.as_view(), name='house-user-list'),
    path('<uuid:house_id>/users/invite/', HouseUserInviteView.as_view(), name='house-user-invite'),
    path('<uuid:house_id>/users/<uuid:user_id>/', HouseUserDetailView.as_view(), name='house-user-detail'),
]
