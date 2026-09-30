from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q, ProtectedError

from apps.catalogo.models import Categoria, Marca, Producto
from apps.catalogo.serializers import CategoriaSerializer, MarcaSerializer, ProductoSerializer
from apps.catalogo.filters import ProductoFilter
from apps.usuarios.permissions import IsAdminOrReadOnly
from apps.usuarios.models import CustomUser

# ==============================================================================
# VIEWSETS DE LA API REST (DRF)
# ==============================================================================

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Categorías.
    Público: GET /api/categorias/
    Administrador: POST, PUT, PATCH, DELETE /api/categorias/
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['nombre', 'slug']
    ordering = ['nombre']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.productos.exists():
            return Response(
                {
                    "error": "No se puede eliminar la categoría porque contiene productos asociados.",
                    "status": status.HTTP_409_CONFLICT
                },
                status=status.HTTP_409_CONFLICT
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    "error": "No se puede eliminar la categoría porque contiene productos asociados.",
                    "status": status.HTTP_409_CONFLICT
                },
                status=status.HTTP_409_CONFLICT
            )


class MarcaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Marcas.
    Público: GET /api/marcas/
    Administrador: POST, PUT, PATCH, DELETE /api/marcas/
    """
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['nombre', 'slug']
    ordering = ['nombre']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.productos.exists():
            return Response(
                {
                    "error": "No se puede eliminar la marca porque contiene productos asociados.",
                    "status": status.HTTP_409_CONFLICT
                },
                status=status.HTTP_409_CONFLICT
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    "error": "No se puede eliminar la marca porque contiene productos asociados.",
                    "status": status.HTTP_409_CONFLICT
                },
                status=status.HTTP_409_CONFLICT
            )


class ProductoViewSet(viewsets.ModelViewSet):
    """
    CRUD y Consulta del Catálogo de Productos.
    
    Permisos:
    - Público/Clientes: Solo lectura (GET /api/productos/, GET /api/productos/{id}/)
      y únicamente de productos con activo=True.
    - Administrador: CRUD completo (POST, PUT, PATCH, DELETE).
    
    Baja lógica:
    - DELETE realiza activo=False para proteger historial de compras.
    """
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductoFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'sku', 'marca__nombre']
    ordering_fields = ['precio', 'nombre', 'stock', 'creado_en']
    ordering = ['-id']

    def get_queryset(self):
        user = self.request.user
        base_qs = Producto.objects.select_related('categoria', 'marca')
        
        # Administradores pueden ver todos los productos (incluyendo inactivos para gestión)
        if user.is_authenticated and (getattr(user, 'role', None) == CustomUser.Role.ADMINISTRADOR or user.is_superuser):
            return base_qs.all()
        
        # Público y Clientes regulares solo pueden ver productos activos para la venta
        return base_qs.filter(activo=True)

    def destroy(self, request, *args, **kwargs):
        """
        Baja lógica: En lugar de borrar la fila física en PostgreSQL,
        desactiva el producto (activo=False) para salvaguardar la integridad de órdenes históricas.
        """
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(
            {
                "mensaje": f"Producto '{instance.nombre}' desactivado exitosamente (baja lógica).",
                "id": instance.id,
                "activo": False
            },
            status=status.HTTP_200_OK
        )


# ==============================================================================
# VISTAS WEB (DJANGO TEMPLATES)
# ==============================================================================

class CatalogoListView(ListView):
    """
    Vista web funcional para listar y filtrar el catálogo público de productos.
    Soporta búsqueda multi-campo (nombre, SKU, marca, categoría) y filtros por ID o slug.
    """
    model = Producto
    template_name = 'catalogo/productos.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        qs = Producto.objects.filter(activo=True).select_related('categoria', 'marca')
        
        # Filtro de búsqueda por texto (nombre, SKU, marca, categoría)
        q = self.request.GET.get('q')
        if q:
            q_clean = q.strip()
            qs = qs.filter(
                Q(nombre__icontains=q_clean)
                | Q(sku__icontains=q_clean)
                | Q(marca__nombre__icontains=q_clean)
                | Q(categoria__nombre__icontains=q_clean)
            )
            
        # Filtro por categoría (acepta ID numérico o slug/nombre)
        categoria = self.request.GET.get('categoria')
        if categoria:
            val_cat = str(categoria).strip()
            if val_cat.isdigit():
                qs = qs.filter(categoria_id=int(val_cat))
            else:
                qs = qs.filter(
                    Q(categoria__slug__iexact=val_cat) | Q(categoria__nombre__iexact=val_cat)
                )
            
        # Filtro por marca (acepta ID numérico o slug/nombre)
        marca = self.request.GET.get('marca')
        if marca:
            val_marca = str(marca).strip()
            if val_marca.isdigit():
                qs = qs.filter(marca_id=int(val_marca))
            else:
                qs = qs.filter(
                    Q(marca__slug__iexact=val_marca) | Q(marca__nombre__iexact=val_marca)
                )
            
        # Filtro por disponibilidad
        disponible = self.request.GET.get('disponible')
        if disponible:
            disp_clean = str(disponible).strip().lower()
            if disp_clean in ('1', 'true', 'si', 'yes'):
                qs = qs.filter(stock__gt=0)
            elif disp_clean in ('0', 'false', 'no'):
                qs = qs.filter(stock=0)
            
        return qs.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        context['marcas'] = Marca.objects.all().order_by('nombre')
        context['current_q'] = self.request.GET.get('q', '').strip()
        context['current_categoria'] = self.request.GET.get('categoria', '').strip()
        context['current_marca'] = self.request.GET.get('marca', '').strip()
        context['current_disponible'] = self.request.GET.get('disponible', '').strip()
        return context


class ProductoDetailView(DetailView):
    """
    Vista web para el detalle individual de un producto.
    """
    model = Producto
    template_name = 'catalogo/detalle_producto.html'
    context_object_name = 'producto'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Si está inactivo y el usuario no es admin, lanzar 404
        if not obj.activo:
            user = self.request.user
            if not (user.is_authenticated and (getattr(user, 'role', None) == CustomUser.Role.ADMINISTRADOR or user.is_superuser)):
                raise Http404("El producto no está disponible.")
        return obj
