from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para PupeFactory.
    Extiende AbstractUser para aprovechar el sistema nativo de hashing de Django
    (set_password, check_password, grupos y permisos) e incorpora un campo de rol.
    """

    class Role(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENTE,
        verbose_name='Rol del Usuario',
        help_text='Define si el usuario es un cliente regular o un administrador de la tienda.'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['id']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_cliente(self):
        return self.role == self.Role.CLIENTE

    @property
    def is_administrador(self):
        return self.role == self.Role.ADMINISTRADOR or self.is_superuser
