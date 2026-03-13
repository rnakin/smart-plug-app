"""
Alert URL patterns scoped to a house.
Included under /api/houses/<house_id>/ by house/urls.py
"""
from django.urls import path
from .views import (
    AlertRuleListCreateView,
    AlertRuleDetailView,
    AlertEventListView,
    AlertEventActionView,
    AlertTriggerView,
)

urlpatterns = [
    path('alerts/rules/', AlertRuleListCreateView.as_view(), name='alert-rule-list'),
    path('alerts/rules/<uuid:rule_id>/', AlertRuleDetailView.as_view(), name='alert-rule-detail'),
    path('alerts/events/', AlertEventListView.as_view(), name='alert-event-list'),
    path('alerts/events/<uuid:event_id>/action/', AlertEventActionView.as_view(), name='alert-event-action'),
    path('alerts/trigger/', AlertTriggerView.as_view(), name='alert-trigger'),
]
