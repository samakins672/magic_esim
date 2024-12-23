from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/esim/", include("esim.urls")),  # eSIM endpoints
    # path("billing/", include("billing.urls")),  # Billing endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="swagger-ui",
    ),
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("signup/", TemplateView.as_view(template_name="signup.html"), name="signup"),
    path("reset-pasword/", TemplateView.as_view(template_name="reset-pasword.html"), name="reset-pasword"),
    path("dashboard/", TemplateView.as_view(template_name="dashboard.html"), name="dashboard"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
