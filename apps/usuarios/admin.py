from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Configuración en Django Admin para CustomUser.
    Permite gestionar usuarios respetando el hashing nativo de contraseñas
    y añade el campo de rol en los formularios de listado y edición.
    """
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Rol de Usuario', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rol de Usuario', {'fields': ('role',)}),
    )
