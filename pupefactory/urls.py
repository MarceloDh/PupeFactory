"""
Enrutador principal de URLs para PupeFactory.
Incluye endpoints de autenticación, documentación privada protegida y handler404.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import (
    home_view,
    ProtectedSpectacularAPIView,
    ProtectedSpectacularSwaggerView,
    ProtectedSpectacularRedocView,
    error_404_view,
)

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Página de Inicio (Home)
    path('', home_view, name='home'),

    # Módulo de Usuarios y Autenticación (JWT + Sesiones Web)
    path('', include('apps.usuarios.urls')),

    # Módulo de Catálogo (API REST /api/productos/, /api/categorias/, /api/marcas/ + Vistas Web)
    path('', include('apps.catalogo.urls')),

    # Documentación Swagger / OpenAPI PRIVADA (Restringida a Administradores)
    path('api/schema/', ProtectedSpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', ProtectedSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', ProtectedSpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Manejador global oficial para errores 404 en producción
handler404 = error_404_view

# Servir archivos multimedia y estáticos en entorno de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Captura de rutas no encontradas (404 => RE_PATH indicado en pizarra de clase)
# Permite renderizar la vista 404 personalizada de forma inmediata
urlpatterns += [
    re_path(r'^.*$', error_404_view, name='catch_all_404'),
]

