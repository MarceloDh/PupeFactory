from django.shortcuts import render
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.usuarios.permissions import IsAdminRole

# ==============================================================================
# VISTA PRINCIPAL TEMPORAL (HOME)
# ==============================================================================

def home_view(request):
    """
    Renderiza la página principal (Home) de PupeFactory.
    Carga categorías y productos destacados con imágenes para el panel principal.
    """
    from apps.catalogo.models import Producto, Categoria
    categorias = Categoria.objects.all().order_by('nombre')
    productos_destacados = Producto.objects.filter(activo=True).select_related('categoria', 'marca').order_by('-id')[:4]
    
    context = {
        'categorias': categorias,
        'productos_destacados': productos_destacados,
    }
    return render(request, 'home.html', context)



# ==============================================================================
# VISTAS DE DOCUMENTACIÓN SWAGGER / OPENAPI PROTEGIDAS (SOLO ADMINISTRADOR)
# ==============================================================================
# Cumple con el requisito de seguridad estricto de la evaluación:
# La documentación de la API y el esquema OpenAPI NO son públicos.
# El backend valida estrictamente que request.user.role sea ADMINISTRADOR.
# ==============================================================================

class ProtectedSpectacularAPIView(SpectacularAPIView):
    """
    Genera el esquema OpenAPI 3.0 (/api/schema/).
    Protegido en backend con IsAdminRole.
    """
    permission_classes = [IsAdminRole]


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    """
    Renderiza la interfaz gráfica Swagger UI (/api/docs/).
    Protegido en backend con IsAdminRole.
    """
    permission_classes = [IsAdminRole]


class ProtectedSpectacularRedocView(SpectacularRedocView):
    """
    Renderiza la interfaz gráfica ReDoc (/api/redoc/).
    Protegido en backend con IsAdminRole.
    """
    permission_classes = [IsAdminRole]


# ==============================================================================
# VISTA DE ERROR 404 PERSONALIZADA
# ==============================================================================

def error_404_view(request, exception=None):
    """
    Renderiza la plantilla 404.html personalizada de PupeFactory
    cuando una ruta web no existe, sin mostrar trazas del servidor.
    """
    return render(request, 'errors/404.html', status=404)
