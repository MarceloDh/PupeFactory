from apps.usuarios.models import CustomUser


def carro_context(request):
    """
    Context processor que inyecta la cantidad real de ítems en el carro (cart_total_items)
    en todas las plantillas HTML para usuarios autenticados con rol CLIENTE.
    Para usuarios anónimos o administradores retorna 0.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        if getattr(request.user, 'role', None) == CustomUser.Role.CLIENTE:
            try:
                carrito = getattr(request.user, 'carrito', None)
                if carrito:
                    return {'cart_total_items': carrito.total_items}
            except Exception:
                pass
    return {'cart_total_items': 0}
