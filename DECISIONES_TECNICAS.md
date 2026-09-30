# REGISTRO DE DECISIONES TÉCNICAS — PUPEFACTORY (EVA-2)

Este documento recopila las decisiones de arquitectura, modelo y diseño adoptadas en el proyecto para su posterior justificación técnica.

---

## Fase 1: Entorno, Base de Datos y Modelado 3FN
- **Modelo de Usuario:** Se extendió `AbstractUser` en `CustomUser` para reutilizar el hashing seguro PBKDF2/SHA256, autenticación y permisos de Django, incorporando `Role.choices` (`CLIENTE` y `ADMINISTRADOR`).
- **AUTH_USER_MODEL Temprano:** Se fijó antes de la migración inicial para evitar conflictos en llaves foráneas con tablas del core de Django.
- **Normalización 3FN:** Categorías y Marcas se aislaron en tablas maestras. El Producto solo almacena llaves foráneas indexadas, evitando dependencias transitivas.
- **Precio Histórico en OrdenItem:** `OrdenItem.precio_unitario` congela el valor del producto al momento exacto de la compra. Permite que `Producto.precio` varíe en el futuro sin alterar registros históricos contables.
- **Carro Persistente 1 a 1:** Relación `OneToOneField` entre `Usuario` y `Carrito`, persistida directamente en PostgreSQL para sobrevivir a logouts y cambios de dispositivo.
- **Integridad a nivel de Base de Datos:** Se implementaron `CheckConstraint` (precios positivos, stock no negativo, cantidades mayores a cero) y `UniqueConstraint` en `(carrito, producto)` y `sku`.
- **Integridad de Productos Vendidos:** En `OrdenItem`, la llave foránea hacia `Producto` utiliza `on_delete=models.PROTECT`. La eliminación administrativa de un producto aplica baja lógica (`activo = False`).
- **Seguridad en Configuración:** Se exigieron variables de entorno estrictas con `os.environ['...']` en `settings.py` sin credenciales hardcodeadas por defecto.

---

## Fase 2: Autenticación, Roles y Swagger Privado
- **Claims JWT vs. Autorización en Backend:** Los tokens JWT incluyen claims de información (`user_id`, `username`, `role`), pero las clases de permiso (`IsAdminRole`, `IsClienteRole`) siempre validan el estado de `request.user.role` en el servidor.
- **Doble Esquema de Autenticación:** Se utiliza `SessionAuthentication` para vistas web (Django Templates) y `JWTAuthentication` para la API REST. Ambos sistemas comparten la misma tabla de usuarios `usuarios_customuser`.
- **Distinción de Roles:** `role == ADMINISTRADOR` es la regla de negocio del dominio PupeFactory; `is_staff` se reserva exclusivamente para el acceso al panel `/admin/`.
- **Swagger Privado en Backend:** La documentación `/api/docs/` y el esquema `/api/schema/` están protegidos por backend mediante `permission_classes = [IsAdminRole]`. Un usuario anónimo recibe 401 y un cliente recibe 403.
- **Manejo Limpio de Errores:** Se implementó `custom_exception_handler` en DRF para estandarizar respuestas de error en JSON sin exponer stack traces ni detalles del servidor.
- **Seguridad en Comandos de Prueba:** El comando `crear_usuarios_prueba` valida que `settings.DEBUG == True`, abortando su ejecución en modo producción.

---

## Fase 3: Catálogo, Filtros y CRUD Administrativo
- **Visibilidad Pública Filtrada:** Los endpoints públicos del catálogo solo retornan productos con `activo=True`.
- **Baja Lógica Administrativa:** El método `DELETE /api/productos/{id}/` ejecuta un soft-delete (`producto.activo = False`), preservando la integridad referencial en órdenes históricas.
- **Filtrado Real con django-filter:** Implementación de `ProductoFilter` para búsqueda por categoría, marca, rangos de precio (`precio_min`, `precio_max`) y disponibilidad de stock.
- **Búsqueda Multi-campo con SearchFilter:** Búsqueda flexible por nombre de producto, SKU exacto y nombre de marca.

---

## Fase 3.5: Rediseño Visual del Catálogo e Integración de Imágenes
- **Estrategia Híbrida de Imágenes en Producto:** Se incorporó el campo `imagen_url = models.URLField(blank=True, null=True)` mediante migración `0002_producto_imagen_url`, manteniendo la coexistencia con `imagen = models.ImageField(...)`. Se implementó la property de modelo `get_imagen_url` con cascada de prioridad: (1) Archivo local en `media/` (`imagen.url`), (2) URL externa directa (`imagen_url`), (3) Fallback vectorial SVG neutro en plantilla.
- **Tipado Explícito en Serializer para drf-spectacular:** Se agregó `imagen_final = serializers.CharField(source='get_imagen_url', read_only=True, allow_null=True)` al `ProductoSerializer`, asegurando compatibilidad OpenAPI 3.0 sin advertencias de introspección.
- **Estética E-Commerce Retail (Referencia Mwave):** Se migró desde una apariencia de dashboard oscuro a una interfaz e-commerce retail con fondo claro (`#F5F6F8`), tarjetas blancas (`#FFFFFF`), tipografía Google Fonts `Poppins` y acento de marca rosado (`#EC3E8F`).
- **Iconografía Vectorial SVG Inline:** Se eliminaron todos los emojis de la interfaz, reemplazándolos por SVGs inline estandarizados tipo Lucide/Heroicons (`stroke-width: 2`, `currentColor`), sin necesidad de añadir librerías JS externas.
- **Centralización de Estilos en CSS Nativo:** Se consolidó el diseño en `static/css/pupefactory.css` con variables CSS (`:root`), estructurando layout de 2 columnas (sidebar izquierda de filtros + grid derecha de productos), card de producto retail y vistas de login/404 coherentes.
- **Identidad de Marca y Carrusel Promocional (Panel Principal):** Se integró el logotipo oficial `logo.png` (isotipo felino PF + tipografía comercial) en el encabezado y un carrusel dinámico en `home.html` con 4 banners en alta resolución (`banner_1_gpus.png`, `banner_2_setup.png`, `banner_3_speed.png`, `banner_4_cpus.png`), soporte táctil/teclado, navegación por puntos y enlace directo al catálogo por categorías.


