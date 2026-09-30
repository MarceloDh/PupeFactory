import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.usuarios.models import CustomUser

# ==============================================================================
# COMANDO PARA CREAR USUARIOS DE PRUEBA (SOLO DESARROLLO / DEBUG=True)
# ==============================================================================
# Uso: python manage.py crear_usuarios_prueba
# Exclusivamente para agilizar pruebas locales y demostraciones en desarrollo.
# Por seguridad, este comando se bloquea automáticamente si DEBUG=False.
# ==============================================================================

class Command(BaseCommand):
    help = 'Crea o actualiza usuarios de prueba (cliente_test y admin_test). Solo habilitado en desarrollo (DEBUG=True).'

    def handle(self, *args, **options):
        # Medida de seguridad estricta: abortar si no es entorno de desarrollo
        if not settings.DEBUG:
            raise CommandError("Operación bloqueada: Este comando solo puede ejecutarse en modo desarrollo (DEBUG=True).")

        cliente_password = os.environ.get('CLIENTE_TEST_PASSWORD')
        if not cliente_password:
            raise CommandError(
                "Falta la variable de entorno obligatoria 'CLIENTE_TEST_PASSWORD'. "
                "Configúrala en tu archivo .env antes de ejecutar este comando."
            )

        admin_password = os.environ.get('ADMIN_TEST_PASSWORD')
        if not admin_password:
            raise CommandError(
                "Falta la variable de entorno obligatoria 'ADMIN_TEST_PASSWORD'. "
                "Configúrala en tu archivo .env antes de ejecutar este comando."
            )

        # 1. Crear / Actualizar Cliente de Prueba
        cliente, created = CustomUser.objects.get_or_create(
            username='cliente_test',
            defaults={
                'email': 'cliente@pupefactory.cl',
                'first_name': 'Cliente',
                'last_name': 'Prueba',
                'role': CustomUser.Role.CLIENTE,
                'is_staff': False,
                'is_active': True,
            }
        )
        cliente.set_password(cliente_password)
        cliente.role = CustomUser.Role.CLIENTE
        cliente.is_staff = False
        cliente.save()
        status_cliente = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Usuario {cliente.username} ({status_cliente}) - Rol: {cliente.role}"))

        # 2. Crear / Actualizar Administrador de Prueba
        admin, created = CustomUser.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@pupefactory.cl',
                'first_name': 'Admin',
                'last_name': 'Prueba',
                'role': CustomUser.Role.ADMINISTRADOR,
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
            }
        )
        admin.set_password(admin_password)
        admin.role = CustomUser.Role.ADMINISTRADOR
        admin.is_staff = True
        admin.save()
        status_admin = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Usuario {admin.username} ({status_admin}) - Rol: {admin.role}"))

        self.stdout.write(self.style.SUCCESS("\n[OK] Usuarios de desarrollo listos para pruebas."))
