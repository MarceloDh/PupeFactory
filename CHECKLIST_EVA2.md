# CHECKLIST EVALUACIÓN EVA-2 — BACKEND (GRUPO 1: PUPEFACTORY)

> **Asignatura:** Desarrollo Backend  
> **Proyecto:** Tienda de Hardware y Componentes PC (PupeFactory)  
> **Ponderación:** 25% total asignatura (30% Desarrollo Técnico + 70% Defensa Oral)  
> **Puntaje Total:** 100 Puntos  

---

## Leyenda de Estados
- `[ ]` Pendiente
- `[x]` Implementado y Probado
- `[!]` En revisión / Por validar

---

## 1. Pauta de Cotejo Técnica (Checklist de Entrega Oficial)

| Elemento | Requerimiento Técnico | Estado | Verificación / Archivos |
| :--- | :--- | :---: | :--- |
| **Base de Datos** | Conexión activa a PostgreSQL en `settings.py` (`django.db.backends.postgresql`) | [x] | `pupefactory/settings.py` y `pupefactory_db` |
| **Documentación** | Swagger / OpenAPI operativo en `/api/docs/` (restringido a administradores) | [x] | `drf-spectacular`, `core/views.py` (Probado: admin 200, cliente 403, anónimo 401) |
| **Comentarios** | Código documentado en bloques explícitos indicando la lógica | [x] | Todos los modelos y configuraciones (.py) |
| **Datos Alumno** | Nombre Completo, Sección y Año presentes en la vista/footer base | [x] | `templates/base.html`, `apps/core/context_processors.py` |
| **Modelos** | Atributo con `CHOICES` definido (estados de orden/transacción) | [x] | `apps/ordenes/models.py` (`Orden.Estado.choices`) |
| **Filtros** | `django-filter` configurado en endpoints de consulta (`/api/productos/`) | [x] | `apps/catalogo/filters.py` (Categoría, marca, precio_min, precio_max, disponible) |
| **Autenticación** | Login JWT retornando tokens (access/refresh) y claims de rol | [x] | `apps/usuarios/serializers.py` (`user_id`, `username`, `role`) |
| **Carro** | Persistencia post-logout en PostgreSQL (relación 1:1 con usuario) | [!] | Modelo `Carrito` (1:1) en PostgreSQL (endpoints en Fase 4) |
| **Stock/Cupos** | Validación y descuento atómico al cambiar a estado `PAGADO` | [ ] | `apps/ordenes/services.py` |

---

## 2. Requerimientos de la Rúbrica Analítica (30% Desarrollo Backend)

### 2.1 Conexión DB, CHOICES y Filtros (6 Pts)
- [x] Configuración nativa de motor PostgreSQL (`psycopg` / `psycopg2-binary`).
- [x] Modelos relacionados con integridad referencial (ForeignKeys, OneToOne).
- [x] Implementación de `CHOICES` explícito en estados de orden (`PENDIENTE`, `PAGADO`, `ENTREGADO`, `CANCELADO`).
- [x] `django-filter` implementado con filtros por categoría, marca, rango de precio (`min_price`, `max_price`), disponibilidad.
- [x] Búsqueda por texto (nombre, marca, SKU).

### 2.2 Autenticación JWT y Roles (8 Pts)
- [x] Endpoints de token JWT (`/api/auth/token/`, `/api/auth/token/refresh/`).
- [x] Inclusión de claims personalizados en el payload JWT (`role`: `CLIENTE` o `ADMINISTRADOR`, `username`, `user_id`).
- [!] Permisos DRF:
  - Lectura pública: `/api/productos/`, `/api/categorias/` [x].
  - Protegido (`IsAuthenticated` / Cliente): `/api/carro/`, `/api/ordenes/checkout/`, `/api/mis-ordenes/` (Fase 4 y 5).
  - Restringido (`IsAdminUser` / `IsAdminRole`): Swagger `/api/docs/` y CRUD productos (`POST`, `PUT`, `PATCH`, `DELETE`) [x]; CRUD órdenes (Fase 5).

### 2.3 Persistencia del Carro de Compras (8 Pts)
- [ ] Relación 1 a 1 entre Usuario y Carro activo en BD PostgreSQL.
- [ ] CarroItem con clave única `(carrito, producto)` para evitar duplicidad de registros del mismo producto.
- [ ] Persistencia garantizada al cerrar sesión o cambiar de dispositivo.
- [ ] Métodos para agregar, actualizar cantidad y eliminar ítems.

### 2.4 Lógica de Stock y Transacciones Atómicas (8 Pts)
- [ ] Agregar al carro **NO** descuenta inventario.
- [ ] Transición de estados de la orden: `PENDIENTE` -> `PAGADO` -> `ENTREGADO` / `CANCELADO`.
- [ ] Descuento de stock únicamente al pasar a `PAGADO`.
- [ ] Uso estricto de transacciones atómicas (`transaction.atomic()`) y bloqueo pesimista (`select_for_update()`) para compras concurrentes.
- [ ] Si stock es insuficiente al pagar, la transacción se cancela/rechaza sin afectar datos.
- [ ] Reposición automática de stock al catálogo si una orden `PAGADO` pasa a `CANCELADO`.
- [ ] Control para evitar doble reposición de inventario.
- [ ] Congelación de precio histórico en `OrdenItem.precio_unitario`.

---

## 3. Requerimientos de Fotografías de la Pizarra y Pautas Adicionales

- [ ] **3FN (Tercera Forma Normal):** Modelo relacional normalizado sin dependencias parciales ni transitivas.
- [ ] **Refactoring Guru / Clean Code:** Separación de responsabilidades, funciones pequeñas, uso de `services.py` para lógica de negocio pesada (checkout, stock).
- [ ] **Error 404 Personalizado:**
  - Template `404.html` estilizado según la identidad visual de la tienda.
  - Botón "Volver al inicio", sin stack traces ni páginas amarillas de depuración.
  - Manejador `handler404` en `urls.py`.
  - Excepciones API limpias en JSON (`{ "error": "Recurso no encontrado.", "status": 404 }`).
- [x] **Protección Estricta de Swagger/OpenAPI:**
  - `/api/docs/` y `/api/schema/` accesibles exclusivamente por usuarios con rol `ADMINISTRADOR`.
  - Clientes y anónimos reciben 403 Forbidden o 401 Unauthorized en backend.
  - Soporte Bearer JWT integrado en Swagger UI.
- [!] **Frontend Django Templates:**
  - Diseño temático "PupeFactory" base (`base.html`, `login.html`, `home.html`, `404.html`).
  - Footer con datos del alumno visible y renderizado en todas las vistas base. [x]
  - Catálogo, detalle, carro y checkout se implementarán en Fases 3 y 4. [ ]

---

## 4. Matriz de Endpoints API Requeridos

| Método | Endpoint | Rol Requerido | Descripción | Estado |
| :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/token/` | Público | Obtener tokens JWT (con claim `role`) | [x] |
| `POST` | `/api/auth/token/refresh/` | Público | Refrescar token access | [x] |
| `GET` | `/api/productos/` | Público | Listado y filtros de productos | [x] |
| `GET` | `/api/productos/{id}/` | Público | Detalle de un producto | [x] |
| `GET` | `/api/categorias/` | Público | Listado de categorías | [x] |
| `GET` | `/api/carro/` | Cliente | Consultar carro activo del usuario | [ ] |
| `POST` | `/api/carro/` | Cliente | Agregar producto o modificar cantidad | [ ] |
| `DELETE` | `/api/carro/{producto_id}/` | Cliente | Eliminar producto del carro | [ ] |
| `POST` | `/api/ordenes/checkout/` | Cliente | Iniciar compra / checkout | [ ] |
| `GET` | `/api/mis-ordenes/` | Cliente | Historial de órdenes del usuario logueado | [ ] |
| `POST` | `/api/productos/` | Administrador | Crear nuevo producto | [x] |
| `PUT/PATCH` | `/api/productos/{id}/` | Administrador | Modificar producto existente | [x] |
| `DELETE` | `/api/productos/{id}/` | Administrador | Desactivar producto (baja lógica `activo=False`) | [x] |
| `PATCH` | `/api/ordenes/{id}/estado/` | Administrador | Cambiar estado de orden (manejo de stock) | [ ] |
| `GET` | `/api/docs/` | Administrador | Documentación Swagger/OpenAPI protegida | [x] |

---

## 5. Preparación para Defensa Oral (70% de la Nota)

- [ ] Explicación de configuración de PostgreSQL y modelo relacional (1:1, 1:N).
- [ ] Justificación de 3FN y precio histórico en `OrdenItem`.
- [ ] Explicación del ciclo JWT: access token, refresh token y claims personalizados.
- [ ] Justificación del carro de compras persistente en base de datos.
- [ ] Explicación de transacciones atómicas (`transaction.atomic`), concurrencia y `select_for_update()`.
- [ ] Explicación de permisos DRF (`IsAuthenticated`, roles personalizados, Swagger protegido).
- [ ] Explicación del sistema de filtros `django-filter` y búsqueda.
- [ ] Justificación de decisiones de refactorización y arquitectura limpia (`services.py`).
