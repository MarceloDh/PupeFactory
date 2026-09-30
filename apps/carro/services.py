from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError
from apps.carro.models import Carrito, CarritoItem
from apps.catalogo.models import Producto
from apps.usuarios.models import CustomUser


class CartService:
    """
    Capa de servicio para la lógica de negocio del Carro de Compras Persistente.
    Centraliza las validaciones de stock, disponibilidad y persistencia 1:1,
    siendo utilizada tanto por la API REST como por las vistas Web tradicionales.
    """

    @staticmethod
    def get_or_create_cart(user):
        """
        Obtiene o crea de forma idempotente el Carrito 1:1 para el usuario cliente.
        Garantiza que el carro esté persistido en la base de datos.
        """
        if not user or not user.is_authenticated:
            raise DRFValidationError({"error": "Usuario no autenticado.", "status": 401})

        carrito, _ = Carrito.objects.get_or_create(usuario=user)
        return carrito

    @classmethod
    def add_item(cls, user, producto_id, cantidad=1):
        """
        Agrega un producto al carro o incrementa su cantidad si ya existe.
        
        Validaciones obligatorias:
        - Producto existe
        - Producto activo=True
        - Cantidad entero positivo (> 0)
        - Producto con stock disponible (> 0)
        - Cantidad acumulada en el carro <= stock disponible del producto
        
        IMPORTANTE: Esta operación NO descuenta inventario (Producto.stock permanece intacto).
        """
        # 1. Validar cantidad básica
        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            raise DRFValidationError({"error": "La cantidad debe ser un número entero válido.", "status": 400})

        if cantidad <= 0:
            raise DRFValidationError({"error": "La cantidad a agregar debe ser mayor a cero.", "status": 400})

        # 2. Validar existencia del producto
        try:
            producto = Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist:
            raise NotFound({"error": "El producto solicitado no existe en el catálogo.", "status": 404})

        # 3. Validar estado activo del producto
        if not producto.activo:
            raise DRFValidationError({"error": "El producto no está disponible para la venta.", "status": 400})

        # 4. Validar stock físico
        if producto.stock <= 0:
            raise DRFValidationError({"error": "El producto se encuentra agotado.", "status": 400})

        # 5. Obtener carro del usuario
        carrito = cls.get_or_create_cart(user)

        # 6. Validar acumulación respecto al stock físico
        item = CarritoItem.objects.filter(carrito=carrito, producto=producto).first()
        cantidad_actual = item.cantidad if item else 0
        cantidad_final = cantidad_actual + cantidad

        if cantidad_final > producto.stock:
            raise DRFValidationError({
                "error": f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.",
                "status": 400
            })

        # 7. Persistir: actualizar cantidad o crear nuevo CarritoItem
        if item:
            item.cantidad = cantidad_final
            item.save(update_fields=['cantidad'])
            created = False
        else:
            item = CarritoItem.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=cantidad
            )
            created = True

        return item, created

    @classmethod
    def update_item_quantity(cls, user, producto_id, nueva_cantidad):
        """
        Actualiza directamente la cantidad de un ítem existente en el carro del usuario.
        
        Validaciones:
        - Ítem existe en el carro del usuario
        - Cantidad entero >= 1
        - Producto activo
        - Cantidad <= stock disponible
        """
        try:
            nueva_cantidad = int(nueva_cantidad)
        except (ValueError, TypeError):
            raise DRFValidationError({"error": "La cantidad debe ser un número entero válido.", "status": 400})

        if nueva_cantidad <= 0:
            raise DRFValidationError({"error": "La cantidad debe ser al menos 1 unidad.", "status": 400})

        carrito = cls.get_or_create_cart(user)
        item = CarritoItem.objects.select_related('producto').filter(carrito=carrito, producto_id=producto_id).first()

        if not item:
            raise NotFound({"error": "El producto no se encuentra en el carro.", "status": 404})

        producto = item.producto
        if not producto.activo:
            raise DRFValidationError({"error": "El producto ya no está disponible para la venta.", "status": 400})

        if nueva_cantidad > producto.stock:
            raise DRFValidationError({
                "error": f"Stock insuficiente. Solo hay {producto.stock} unidades disponibles.",
                "status": 400
            })

        item.cantidad = nueva_cantidad
        item.save(update_fields=['cantidad'])
        return item

    @classmethod
    def remove_item(cls, user, producto_id):
        """
        Elimina un ítem específico del carro del usuario.
        No modifica el stock del producto.
        """
        carrito = cls.get_or_create_cart(user)
        item = CarritoItem.objects.filter(carrito=carrito, producto_id=producto_id).first()

        if not item:
            raise NotFound({"error": "El producto no se encuentra en el carro.", "status": 404})

        item.delete()
        return True

    @classmethod
    def clear_cart(cls, user):
        """
        Elimina todos los ítems del carro del usuario.
        Mantiene intacta la instancia 1:1 de Carrito.
        """
        carrito = cls.get_or_create_cart(user)
        carrito.items.all().delete()
        return True
