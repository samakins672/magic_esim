from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("users.urls")),
    path("esim/", include("esim.urls")),  # eSIM endpoints
    # path("billing/", include("billing.urls")),  # Billing endpoints
    path("schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="swagger-ui",
    ),
]
