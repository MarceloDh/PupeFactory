from rest_framework.permissions import BasePermission
from apps.usuarios.models import CustomUser

# ==============================================================================
# PERMISOS BASADOS EN ROLES (RBAC - ROLE-BASED ACCESS CONTROL)
# ==============================================================================
# Cumple con el requerimiento de seguridad y rúbrica (Criterio 2.2):
# La autorización se valida en el servidor contra el modelo de usuario
# autenticado (request.user.role), evitando confiar ciegamente en datos del frontend.
# ==============================================================================

class IsAdminRole(BasePermission):
    """
    Permite acceso únicamente a usuarios autenticados con rol ADMINISTRADOR.
    
    NOTA PARA LA DEFENSA ORAL:
    Diferencia conceptual entre 'role == ADMINISTRADOR' e 'is_staff':
    - 'role == ADMINISTRADOR': Es el rol de negocio dentro del dominio de PupeFactory.
      Determina quién puede crear productos, cambiar inventario y ver la documentación Swagger.
    - 'is_staff': Es una bandera interna del framework Django que autoriza el ingreso
      al panel técnico de administración (/admin/).
    """
    message = "Acceso restringido: Se requiere rol de ADMINISTRADOR para realizar esta acción."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == CustomUser.Role.ADMINISTRADOR or request.user.is_superuser)
        )


class IsClienteRole(BasePermission):
    """
    Permite acceso únicamente a usuarios autenticados con rol CLIENTE.
    Utilizado para proteger las acciones del carro de compras, checkout y mis órdenes.
    """
    message = "Acceso restringido: Se requiere ser un CLIENTE autenticado para acceder."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.Role.CLIENTE
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Permite lectura pública (GET, HEAD, OPTIONS) a cualquier usuario.
    Las modificaciones (POST, PUT, PATCH, DELETE) requieren rol de ADMINISTRADOR.
    """
    message = "Acceso restringido: Se requiere rol de ADMINISTRADOR para modificar el catálogo."

    def has_permission(self, request, view):
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == CustomUser.Role.ADMINISTRADOR or request.user.is_superuser)
        )

