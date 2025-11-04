# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls", namespace="dashboard")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("users.urls")),  # URLs de gestión de usuarios
    path("projects/", include("projects.urls")),
    path("catalog/", include("catalog.urls")),  # Catálogo de materiales
    path('chatbot/', include('chatbot.urls')),
    path('manual/', include('manual.urls')),  # Manual de usuario
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
