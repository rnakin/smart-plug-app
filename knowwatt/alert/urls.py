"""
Alert API URL patterns.
House-scoped patterns included under /api/houses/<house_id>/ via house/urls.py
Global patterns included under /api/ via knowwatt/urls.py
"""
from django.urls import path
from .views import (
    AlertRuleListCreateView,
    AlertRuleDetailView,
    AlertEventListView,
    AlertEventActionView,
    AlertTriggerView,
    PushTokenView,
    UserNotificationsView,
)

# House-scoped (included under /api/houses/<house_id>/)
house_urlpatterns = [
    path('alerts/rules/', AlertRuleListCreateView.as_view(), name='alert-rule-list'),
    path('alerts/rules/<uuid:rule_id>/', AlertRuleDetailView.as_view(), name='alert-rule-detail'),
    path('alerts/events/', AlertEventListView.as_view(), name='alert-event-list'),
    path('alerts/events/<uuid:event_id>/action/', AlertEventActionView.as_view(), name='alert-event-action'),
    path('alerts/trigger/', AlertTriggerView.as_view(), name='alert-trigger'),
]

# Global (included under /api/)
urlpatterns = [
    path('alerts/push-token/', PushTokenView.as_view(), name='push-token'),
    path('alerts/notifications/', UserNotificationsView.as_view(), name='user-notifications'),
]
