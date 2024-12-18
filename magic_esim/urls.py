from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="eSIM API",
        default_version="v1",
        description="API documentation for eSIM backend",
        contact=openapi.Contact(email="support@yourdomain.com"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("djoser.urls")),  # Djoser auth endpoints
    path("auth/", include("djoser.urls.authtoken")),  # Token endpoints
    path("esim/", include("esim.urls")),  # eSIM endpoints
    # path("billing/", include("billing.urls")),  # Billing endpoints
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),  # Swagger docs
]
