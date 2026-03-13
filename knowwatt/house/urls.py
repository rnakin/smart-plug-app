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

]
