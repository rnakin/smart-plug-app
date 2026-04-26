
from django.contrib import admin
from django.urls import path, include
from device import views

urlpatterns = [
    path('admin/', admin.site.urls),
]

handler404 = 'funt.views.custom_404'

urlpatterns += [
    # Auth (login, register, etc.) - keep existing
    path("auth/", include("account.urls")),

    # Landing / index
    path("", include("funt.urls")),

    # ── Page views (server-side rendered) ──
    path("account/", include("account.page_urls")),
    path("houses/", include("house.page_urls")),
    path("devices/", include("device.page_urls_global")),
    path("houses/<uuid:house_pk>/", include("device.page_urls")),
    path("houses/<uuid:house_pk>/", include("energy.page_urls")),
    path("houses/<uuid:house_pk>/", include("alert.page_urls")),

    # ── API endpoints (keep untouched) ──
    path("api/houses/", include("house.urls")),
    path("api/", include("device.urls")),
    path("api/", include("alert.urls")),
    
    # KnowWatt MQTT & HTMX endpoints
    path("plugs/<str:plug_id>/command/", views.publish_command, name='publish-command'),
    path("plugs/<str:plug_id>/relay-status/", views.relay_status, name='relay-status'),
]
