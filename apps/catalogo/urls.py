from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalogo.views import (
    CategoriaViewSet,
    MarcaViewSet,
    ProductoViewSet,
    CatalogoListView,
    ProductoDetailView,
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'marcas', MarcaViewSet, basename='marca')

urlpatterns = [
    # Endpoints de la API REST (/api/productos/, /api/categorias/, /api/marcas/)
    path('api/', include(router.urls)),

    # Vistas Web Django Templates
    path('catalogo/', CatalogoListView.as_view(), name='catalogo'),
    path('catalogo/<int:pk>/', ProductoDetailView.as_view(), name='producto_detalle'),
]
