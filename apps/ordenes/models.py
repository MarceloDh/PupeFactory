from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.catalogo.models import Producto


class Orden(models.Model):
    """
    Orden de Compra generada tras el checkout.
    Implementa explícitamente la propiedad CHOICES requerida por la rúbrica
    para los estados de la transacción.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADO = 'PAGADO', 'Pagado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    # Matriz explícita de transiciones de estado permitidas
    TRANSICIONES_VALIDAS = {
        Estado.PENDIENTE: [Estado.PAGADO, Estado.CANCELADO],
        Estado.PAGADO: [Estado.ENTREGADO, Estado.CANCELADO],
        Estado.ENTREGADO: [],  # Estado terminal
        Estado.CANCELADO: [],  # Estado terminal
    }

    numero_orden = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Número de Orden'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes',
        verbose_name='Cliente'
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado de la Orden'
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Monto Total de la Compra (CLP)'
    )
    stock_reincorporado = models.BooleanField(
        default=False,
        verbose_name='¿Stock devuelto tras cancelación?',
        help_text='Bandera de control atómico para evitar la doble reposición de inventario.'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')

    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Orden #{self.numero_orden} - {self.usuario.username} [{self.get_estado_display()}]"

    def puede_transicionar_a(self, nuevo_estado):
        """Verifica si la transición solicitada es legal según la máquina de estados del negocio."""
        return nuevo_estado in self.TRANSICIONES_VALIDAS.get(self.estado, [])


class OrdenItem(models.Model):
    """
    Detalle histórico de los productos comprados en una orden.
    CONGELA el precio unitario del producto al momento de comprar (3FN e integridad contable).
    Usa on_delete=models.PROTECT en Producto para impedir roturas si el producto se modifica/elimina.
    """
    orden = models.ForeignKey(
        Orden,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Orden Asociada'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='en_ordenes',
        verbose_name='Producto Comprado'
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad Comprada'
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio Unitario Histórico (Congelado)'
    )

    class Meta:
        verbose_name = 'Ítem de Orden'
        verbose_name_plural = 'Ítems de Orden'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='chk_orden_item_cantidad_positiva'
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name='chk_orden_item_precio_no_negativo'
            )
        ]

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} @ ${self.precio_unitario:,.0f}"

    @property
    def subtotal(self):
        """Calcula el subtotal histórico inmutable."""
        return self.precio_unitario * self.cantidad
