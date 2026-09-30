from rest_framework import serializers
from decimal import Decimal
from apps.catalogo.models import Categoria, Marca, Producto

# ==============================================================================
# SERIALIZADORES DEL CATÁLOGO DE PRODUCTOS (PupeFactory)
# ==============================================================================

class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializador para Categorías (ej: Procesadores, Tarjetas de Video, RAM).
    """
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'slug', 'descripcion']


class MarcaSerializer(serializers.ModelSerializer):
    """
    Serializador para Marcas (ej: ASUS, MSI, AMD, NVIDIA).
    """
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'slug']


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializador para Productos de Hardware.
    Permite lectura detallada (incluye nombres de categoría y marca, y estado de stock)
    y escritura validada para operaciones CRUD administrativas.
    """
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    marca_nombre = serializers.ReadOnlyField(source='marca.nombre')
    disponible = serializers.BooleanField(source='tiene_stock', read_only=True)
    imagen_final = serializers.CharField(source='get_imagen_url', read_only=True, allow_null=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'sku',
            'categoria',
            'categoria_nombre',
            'marca',
            'marca_nombre',
            'descripcion',
            'precio',
            'stock',
            'activo',
            'imagen',
            'imagen_url',
            'imagen_final',
            'disponible',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en', 'disponible', 'imagen_final']

    def validate_precio(self, value):
        """Valida que el precio sea estrictamente positivo."""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("El precio debe ser mayor a cero.")
        return value

    def validate_stock(self, value):
        """Valida que el stock no sea negativo."""
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo.")
        return value

    def validate_sku(self, value):
        """Valida que el SKU sea único en el catálogo."""
        sku_clean = value.strip().upper()
        qs = Producto.objects.filter(sku__iexact=sku_clean)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un producto registrado con este código SKU.")
        return sku_clean
