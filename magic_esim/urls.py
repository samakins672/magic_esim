from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls import handler404
from billing.views import MastercardCheckoutCallbackView
from .views import custom_404

urlpatterns = [
    # API Routes
    path("api/admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/esim/", include("esim.urls")),
    path("api/", include("billing.urls")),
    path("api/number/", include("virtual_number.urls")),

    # OpenAPI Schema and Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="swagger-ui",
    ),

    # Frontend Routes
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='frontend_login'),
    path('new/login/', auth_views.LoginView.as_view(template_name='new/login.html'), name='new_frontend_login'),
    path(
        "payments/mastercard/callback/",
        MastercardCheckoutCallbackView.as_view(),
        name="mastercard-checkout-callback",
    ),
    path("", include("frontend.urls")),  # Include frontend URLs
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = custom_404
