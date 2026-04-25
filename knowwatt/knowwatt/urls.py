
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (login, register, etc.) - keep existing
    path("auth/", include("account.urls")),

    # Landing / index
    path("", include("funt.urls")),

    # ── Page views (server-side rendered) ──
    path("account/", include("account.page_urls")),
    path("houses/", include("house.page_urls")),
    path("houses/<uuid:house_pk>/", include("device.page_urls")),
    path("houses/<uuid:house_pk>/", include("energy.page_urls")),
    path("houses/<uuid:house_pk>/", include("alert.page_urls")),

    # ── API endpoints (keep untouched) ──
    path("api/houses/", include("house.urls")),
    path("api/", include("device.urls")),
    path("api/", include("alert.urls")),
]
