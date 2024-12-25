from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API Routes
    path("api/admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/esim/", include("esim.urls")),
    path("api/", include("billing.urls")),
    
    # Frontend Routes
    path("", include("frontend.urls")),  # Include frontend URLs
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
