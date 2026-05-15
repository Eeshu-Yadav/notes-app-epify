"""Root URL configuration — endpoints live at the root per assignment spec."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("notes.urls")),
    path("", include("core.urls")),
    path("openapi.json", SpectacularAPIView.as_view(), name="openapi-schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="openapi-schema"), name="swagger-ui"),
]
