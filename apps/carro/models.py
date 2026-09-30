from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.catalogo.models import Producto


class Carrito(models.Model):
    """
    Carro de compras persistente.
    Cumple con el requerimiento de la rúbrica: Relación 1 a 1 entre el Usuario y su Carro activo en base de datos.
    Persiste en PostgreSQL tras logout o cambio de dispositivo.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito',
        verbose_name='Usuario Propietario'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Modificación')

    class Meta:
        verbose_name = 'Carro de Compras'
        verbose_name_plural = 'Carros de Compras'

    def __str__(self):
        return f"Carro de {self.usuario.username}"

    @property
    def total(self):
        """Calcula el total monetario actual sumando los subtotales de cada ítem."""
        return sum(item.subtotal for item in self.items.select_related('producto'))

    @property
    def total_items(self):
        """Retorna la cantidad total de unidades contenidas en el carro."""
        return sum(item.cantidad for item in self.items.all())


class CarritoItem(models.Model):
    """
    Ítem individual contenido dentro de un carro de compras.
    No duplica registros para un mismo producto (UniqueConstraint).
    """
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Carro Asociado'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='en_carros',
        verbose_name='Producto'
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad Solicitada'
    )
    agregado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha en que se agregó')

    class Meta:
        verbose_name = 'Ítem de Carrito'
        verbose_name_plural = 'Ítems de Carrito'
        constraints = [
            models.UniqueConstraint(
                fields=['carrito', 'producto'],
                name='unique_carrito_producto'
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='chk_carrito_item_cantidad_positiva'
            )
        ]

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} en Carro de {self.carrito.usuario.username}"

    @property
    def subtotal(self):
        """Calcula el costo del ítem según el precio actual del catálogo."""
        return self.producto.precio * self.cantidad
