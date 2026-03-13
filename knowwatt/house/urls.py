from django.urls import path, include
from .views import (
    HouseListCreateView,
    HouseDetailView,
    HouseUserListView,
    HouseUserInviteView,
    HouseUserManageView,
)

urlpatterns = [
    # House list / create
    path('', HouseListCreateView.as_view(), name='house-list-create'),
    path('<uuid:house_id>/', HouseDetailView.as_view(), name='house-detail'),

    # Member management
    path('<uuid:house_id>/users/', HouseUserListView.as_view(), name='house-user-list'),
    path('<uuid:house_id>/users/invite/', HouseUserInviteView.as_view(), name='house-user-invite'),
    path('<uuid:house_id>/users/manage/', HouseUserManageView.as_view(), name='house-user-manage'),

    # Device & NFC (scoped to house) — include device app's house-scoped urls
    path('<uuid:house_id>/', include('device.house_urls')),
]
