from django.urls import path
from apps.carro.views import (
    CarritoAPIView,
    CarritoItemDetailAPIView,
    CarroDetalleWebView,
    CarroAgregarWebView,
    CarroActualizarWebView,
    CarroEliminarWebView,
    CarroVaciarWebView,
)

urlpatterns = [
    # API REST (JWT Authentication / IsClienteRole)
    path('api/carro/', CarritoAPIView.as_view(), name='api-carro'),
    path('api/carro/<int:producto_id>/', CarritoItemDetailAPIView.as_view(), name='api-carro-item'),

    # Vistas Web (Django Templates / SessionAuthentication)
    path('carro/', CarroDetalleWebView.as_view(), name='carro_detalle'),
    path('carro/agregar/<int:producto_id>/', CarroAgregarWebView.as_view(), name='carro_agregar'),
    path('carro/item/<int:producto_id>/actualizar/', CarroActualizarWebView.as_view(), name='carro_actualizar'),
    path('carro/item/<int:producto_id>/eliminar/', CarroEliminarWebView.as_view(), name='carro_eliminar'),
    path('carro/vaciar/', CarroVaciarWebView.as_view(), name='carro_vaciar'),
]
