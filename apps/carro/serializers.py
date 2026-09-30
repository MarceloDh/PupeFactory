from rest_framework import serializers
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field
from apps.carro.models import Carrito, CarritoItem


class CarritoItemSerializer(serializers.ModelSerializer):
    """
    Serializador para ítems individuales del carro de compras.
    Calcula dinámicamente precios actuales del catálogo y disponibilidad.
    """
    producto_id = serializers.IntegerField(source='producto.id', read_only=True)
    nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)
    imagen = serializers.CharField(source='producto.get_imagen_url', read_only=True, allow_null=True)
    precio_unitario = serializers.DecimalField(
        source='producto.precio',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    stock_disponible = serializers.IntegerField(source='producto.stock', read_only=True)
    disponible = serializers.SerializerMethodField()

    class Meta:
        model = CarritoItem
        fields = [
            'id',
            'producto_id',
            'nombre',
            'sku',
            'imagen',
            'precio_unitario',
            'cantidad',
            'subtotal',
            'stock_disponible',
            'disponible',
        ]
        read_only_fields = ['id', 'producto_id', 'nombre', 'sku', 'imagen', 'precio_unitario', 'subtotal', 'stock_disponible', 'disponible']

    @extend_schema_field(serializers.BooleanField)
    def get_disponible(self, obj) -> bool:
        return bool(obj.producto.activo and obj.producto.stock > 0)


class CarritoSerializer(serializers.ModelSerializer):
    """
    Serializador para el carro de compras persistente.
    Presenta la relación 1:N con sus ítems, cantidad total y monto total actual.
    """
    usuario = serializers.IntegerField(source='usuario.id', read_only=True)
    items = CarritoItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Carrito
        fields = [
            'id',
            'usuario',
            'items',
            'total_items',
            'total',
            'actualizado_en'
        ]
        read_only_fields = fields


class AgregarItemSerializer(serializers.Serializer):
    """
    Serializador para la carga de productos al carro (POST /api/carro/).
    """
    producto_id = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text='ID del producto a agregar al carro.'
    )
    cantidad = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text='Cantidad de unidades a incorporar (por defecto 1).'
    )


class ActualizarItemSerializer(serializers.Serializer):
    """
    Serializador para actualizar cantidad de un ítem (PATCH /api/carro/{producto_id}/).
    """
    cantidad = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text='Nueva cantidad total para el ítem.'
    )
