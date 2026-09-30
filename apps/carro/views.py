from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.carro.models import Carrito, CarritoItem
from apps.carro.services import CartService
from apps.carro.serializers import (
    CarritoSerializer,
    CarritoItemSerializer,
    AgregarItemSerializer,
    ActualizarItemSerializer,
)
from apps.usuarios.permissions import IsClienteRole
from apps.usuarios.models import CustomUser


# ==============================================================================
# CONTROLADORES DE LA API REST (DRF - SIMPLE JWT)
# ==============================================================================

class CarritoAPIView(APIView):
    """
    Gestión del carro de compras persistente del usuario cliente.
    Restringido exclusivamente a usuarios autenticados con rol CLIENTE.
    """
    permission_classes = [IsClienteRole]

    @extend_schema(
        summary="Consultar carro de compras activo",
        description="Retorna el carro activo del cliente autenticado con precios actuales del catálogo.",
        responses={
            200: CarritoSerializer,
            401: OpenApiResponse(description="Autenticación requerida."),
            403: OpenApiResponse(description="Solo clientes pueden acceder al carro."),
        }
    )
    def get(self, request):
        carrito = CartService.get_or_create_cart(request.user)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Agregar producto al carro de compras",
        description="Agrega un producto al carro o incrementa su cantidad si ya existe. Valida disponibilidad y stock.",
        request=AgregarItemSerializer,
        responses={
            200: CarritoSerializer,
            201: CarritoSerializer,
            400: OpenApiResponse(description="Stock insuficiente, producto inactivo o cantidad no válida."),
            404: OpenApiResponse(description="Producto no encontrado."),
        }
    )
    def post(self, request):
        serializer = AgregarItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        producto_id = serializer.validated_data['producto_id']
        cantidad = serializer.validated_data.get('cantidad', 1)

        item, created = CartService.add_item(request.user, producto_id, cantidad)
        carrito_serializer = CarritoSerializer(item.carrito)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(carrito_serializer.data, status=status_code)

    @extend_schema(
        operation_id="carro_vaciar",
        summary="Vaciar todos los productos del carro",
        description="Elimina todos los ítems contenidos en el carro manteniendo la instancia Carrito 1:1.",
        responses={
            200: CarritoSerializer,
            401: OpenApiResponse(description="Autenticación requerida."),
        }
    )
    def delete(self, request):
        CartService.clear_cart(request.user)
        carrito = CartService.get_or_create_cart(request.user)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)


class CarritoItemDetailAPIView(APIView):
    """
    Operaciones sobre un ítem específico dentro del carro de compras.
    Restringido exclusivamente a usuarios autenticados con rol CLIENTE.
    """
    permission_classes = [IsClienteRole]

    @extend_schema(
        operation_id="carro_actualizar_item",
        summary="Actualizar cantidad de un producto en el carro",
        description="Modifica directamente la cantidad de unidades solicitadas de un ítem existente.",
        request=ActualizarItemSerializer,
        responses={
            200: CarritoSerializer,
            400: OpenApiResponse(description="Cantidad fuera de rango o stock insuficiente."),
            404: OpenApiResponse(description="El producto no está en el carro."),
        }
    )
    def patch(self, request, producto_id):
        serializer = ActualizarItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nueva_cantidad = serializer.validated_data['cantidad']
        item = CartService.update_item_quantity(request.user, producto_id, nueva_cantidad)
        return Response(CarritoSerializer(item.carrito).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="carro_eliminar_item",
        summary="Eliminar producto del carro de compras",
        description="Elimina el ítem del carro del usuario. No altera el stock del producto.",
        responses={
            200: CarritoSerializer,
            404: OpenApiResponse(description="El producto no se encuentra en el carro."),
        }
    )
    def delete(self, request, producto_id):
        CartService.remove_item(request.user, producto_id)
        carrito = CartService.get_or_create_cart(request.user)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_200_OK)


# ==============================================================================
# VISTAS WEB TRADICIONALES (DJANGO SESSIONS / TEMPLATES)
# ==============================================================================

class CarroDetalleWebView(LoginRequiredMixin, View):
    """
    Vista web que renderiza la plantilla detalle.html con los ítems y totales del carro.
    """
    login_url = '/accounts/login/'

    def get(self, request):
        if getattr(request.user, 'role', None) != CustomUser.Role.CLIENTE and not request.user.is_superuser:
            messages.warning(request, "El acceso al carro de compras está reservado para clientes.")
            return redirect('home')

        carrito = CartService.get_or_create_cart(request.user)
        items = carrito.items.select_related('producto__marca', 'producto__categoria').order_by('-id')

        context = {
            'carrito': carrito,
            'items': items,
        }
        return render(request, 'carro/detalle.html', context)


class CarroAgregarWebView(LoginRequiredMixin, View):
    """
    Procesa la incorporación de productos al carro desde la interfaz web (ej: botón en detalle de producto).
    """
    login_url = '/accounts/login/'

    def post(self, request, producto_id):
        if getattr(request.user, 'role', None) != CustomUser.Role.CLIENTE and not request.user.is_superuser:
            messages.warning(request, "Solo los clientes pueden agregar productos al carro de compras.")
            return redirect('producto_detalle', pk=producto_id)

        cantidad = request.POST.get('cantidad', 1)
        try:
            item, created = CartService.add_item(request.user, producto_id, cantidad)
            messages.success(request, f"Se agregaron {cantidad} un. de '{item.producto.nombre}' al carro.")
        except Exception as e:
            msg = getattr(e, 'detail', str(e))
            if isinstance(msg, dict) and 'error' in msg:
                msg = msg['error']
            messages.error(request, str(msg))

        return redirect('carro_detalle')


class CarroActualizarWebView(LoginRequiredMixin, View):
    """
    Permite incrementar (+), decrementar (-) o ajustar la cantidad de un ítem desde la web.
    """
    login_url = '/accounts/login/'

    def post(self, request, producto_id):
        accion = request.POST.get('accion')
        cantidad = request.POST.get('cantidad')

        try:
            item = CarritoItem.objects.filter(carrito__usuario=request.user, producto_id=producto_id).first()
            if not item:
                messages.error(request, "El producto no se encuentra en el carro.")
                return redirect('carro_detalle')

            if accion == 'incrementar':
                CartService.update_item_quantity(request.user, producto_id, item.cantidad + 1)
            elif accion == 'decrementar':
                if item.cantidad > 1:
                    CartService.update_item_quantity(request.user, producto_id, item.cantidad - 1)
                else:
                    CartService.remove_item(request.user, producto_id)
            elif cantidad:
                CartService.update_item_quantity(request.user, producto_id, cantidad)

        except Exception as e:
            msg = getattr(e, 'detail', str(e))
            if isinstance(msg, dict) and 'error' in msg:
                msg = msg['error']
            messages.error(request, str(msg))

        return redirect('carro_detalle')


class CarroEliminarWebView(LoginRequiredMixin, View):
    """
    Elimina un ítem específico del carro desde la vista web.
    """
    login_url = '/accounts/login/'

    def post(self, request, producto_id):
        try:
            CartService.remove_item(request.user, producto_id)
            messages.info(request, "Producto eliminado del carro.")
        except Exception as e:
            messages.error(request, "No se pudo eliminar el producto del carro.")

        return redirect('carro_detalle')


class CarroVaciarWebView(LoginRequiredMixin, View):
    """
    Vacía todos los productos del carro desde la vista web.
    """
    login_url = '/accounts/login/'

    def post(self, request):
        CartService.clear_cart(request.user)
        messages.info(request, "El carro ha sido vaciado exitosamente.")
        return redirect('carro_detalle')
