from django.urls import path
from . import page_views

urlpatterns = [
    path('alerts/', page_views.alert_event_list, name='page-alert-events'),
    path('alerts/events/<uuid:event_pk>/action/', page_views.alert_event_action, name='page-alert-event-action'),
    path('alerts/rules/', page_views.alert_rule_list, name='page-alert-rules'),
    path('alerts/rules/create/', page_views.alert_rule_create, name='page-alert-rule-create'),
    path('alerts/rules/<uuid:rule_pk>/edit/', page_views.alert_rule_edit, name='page-alert-rule-edit'),
    path('alerts/rules/<uuid:rule_pk>/delete/', page_views.alert_rule_delete, name='page-alert-rule-delete'),
]
