from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Categoria(models.Model):
    """
    Categoría para clasificación de componentes (ej: Procesadores, Tarjetas de Video, RAM).
    Normalizada para cumplir 3FN.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la Categoría')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Slug Identificador')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    """
    Marca o fabricante de los componentes (ej: ASUS, MSI, AMD, NVIDIA, Corsair).
    Normalizada para cumplir 3FN.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la Marca')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Slug Identificador')

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto o componente de hardware a la venta en PupeFactory.
    Cumple con 3FN: no contiene redundancias transitivas.
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Producto')
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código SKU Único',
        help_text='Identificador único de inventario del producto'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Categoría'
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Marca'
    )
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción Detallada')
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio Actual (CLP)'
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='Stock Físico Disponible'
    )
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True,
        verbose_name='Imagen del Producto'
    )
    imagen_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='URL de Imagen Externa',
        help_text='Enlace HTTP/HTTPS a imagen del producto si no se sube archivo local.'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='¿Activo para la venta?',
        help_text='Si se desactiva, no se muestra en el catálogo público pero mantiene integridad histórica en órdenes.'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio__gt=0),
                name='chk_producto_precio_positivo'
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name='chk_producto_stock_no_negativo'
            ),
        ]

    def __str__(self):
        return f"{self.nombre} (SKU: {self.sku}) - ${self.precio:,.0f}"

    @property
    def tiene_stock(self):
        return self.stock > 0

    @property
    def get_imagen_url(self):
        """Retorna la URL local si existe, la URL remota externa o None."""
        if self.imagen:
            try:
                return self.imagen.url
            except Exception:
                pass
        if self.imagen_url:
            return self.imagen_url
        return None
