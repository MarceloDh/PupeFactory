from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.catalogo.models import Categoria, Marca, Producto
from apps.carro.models import Carrito, CarritoItem
from apps.usuarios.models import CustomUser


class CarroTestCase(TestCase):
    """
    Suite de pruebas completa para FASE 4 — Carro de Compras Persistente.
    Cubre los 26 casos obligatorios:
    - Persistencia en base de datos PostgreSQL/SQLite (1:1 usuario a carrito)
    - Acceso estricto por rol (IsClienteRole: anónimo 401, admin 403, cliente 200)
    - Validaciones de negocio y stock físico
    - Prevención de duplicidad de filas CarritoItem
    - Protección contra acceso horizontal e IDOR
    - Integración Web (sesiones, contador en header y detalle)
    """

    def setUp(self):
        # 1. Catálogo base de prueba
        self.categoria = Categoria.objects.create(nombre='Procesadores', slug='procesadores')
        self.marca_amd = Marca.objects.create(nombre='AMD', slug='amd')
        self.marca_intel = Marca.objects.create(nombre='Intel', slug='intel')

        self.prod_stock_5 = Producto.objects.create(
            nombre='Ryzen 7 7800X3D',
            sku='CPU-AMD-7800X3D',
            categoria=self.categoria,
            marca=self.marca_amd,
            precio=Decimal('420000.00'),
            stock=5,
            activo=True
        )

        self.prod_stock_10 = Producto.objects.create(
            nombre='Core i7 14700K',
            sku='CPU-INTEL-14700K',
            categoria=self.categoria,
            marca=self.marca_intel,
            precio=Decimal('390000.00'),
            stock=10,
            activo=True
        )

        self.prod_agotado = Producto.objects.create(
            nombre='Ryzen 5 5600X',
            sku='CPU-AMD-5600X',
            categoria=self.categoria,
            marca=self.marca_amd,
            precio=Decimal('150000.00'),
            stock=0,  # Sin stock disponible
            activo=True
        )

        self.prod_inactivo = Producto.objects.create(
            nombre='Core i5 Antiguo',
            sku='CPU-OLD-001',
            categoria=self.categoria,
            marca=self.marca_intel,
            precio=Decimal('80000.00'),
            stock=4,
            activo=False  # Desactivado
        )

        # 2. Usuarios con roles diferenciados
        self.cliente_a = CustomUser.objects.create_user(
            username='cliente_a',
            email='clientea@pupefactory.cl',
            password='Password123!',
            role=CustomUser.Role.CLIENTE
        )

        self.cliente_b = CustomUser.objects.create_user(
            username='cliente_b',
            email='clienteb@pupefactory.cl',
            password='Password123!',
            role=CustomUser.Role.CLIENTE
        )

        self.admin_user = CustomUser.objects.create_user(
            username='admin_user',
            email='admin@pupefactory.cl',
            password='AdminPassword123!',
            role=CustomUser.Role.ADMINISTRADOR,
            is_staff=True
        )

        # 3. Clientes API REST
        self.client_anon = APIClient()

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.cliente_a)

        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.cliente_b)

        self.client_admin = APIClient()
        self.client_admin.force_authenticate(user=self.admin_user)

        # 4. Cliente Web tradicional (Django Sessions)
        self.web_client_a = Client()
        self.web_client_a.login(username='cliente_a', password='Password123!')

        self.url_carro = reverse('api-carro')

    # --------------------------------------------------------------------------
    # 1. CONSULTA Y CREACIÓN IDEMPOTENTE 1:1
    # --------------------------------------------------------------------------
    def test_01_cliente_get_carrito_vacio(self):
        """1. Cliente consulta carro vacío inicialmente y recibe estructura con totales en 0."""
        response = self.client_a.get(self.url_carro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['usuario'], self.cliente_a.id)
        self.assertEqual(len(data['items']), 0)
        self.assertEqual(data['total_items'], 0)
        self.assertEqual(Decimal(str(data['total'])), Decimal('0.00'))

    def test_02_get_crea_o_obtiene_carrito_1a1(self):
        """2. GET crea automáticamente el Carrito 1:1 si no existía y preserva la misma instancia."""
        self.assertFalse(Carrito.objects.filter(usuario=self.cliente_a).exists())
        response1 = self.client_a.get(self.url_carro)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(Carrito.objects.filter(usuario=self.cliente_a).count(), 1)
        cart_id = response1.data['id']

        response2 = self.client_a.get(self.url_carro)
        self.assertEqual(response2.data['id'], cart_id)
        self.assertEqual(Carrito.objects.filter(usuario=self.cliente_a).count(), 1)

    # --------------------------------------------------------------------------
    # 2. AGREGAR PRODUCTOS Y STOCK NO MODIFICADO
    # --------------------------------------------------------------------------
    def test_03_cliente_agrega_producto(self):
        """3. Cliente agrega producto al carro con éxito (HTTP 201)."""
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': 2}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(Decimal(str(response.data['total'])), Decimal('840000.00'))

    def test_04_agregar_producto_no_reduce_stock(self):
        """4. Agregar producto al carro NO descuenta inventario (Producto.stock permanece intacto)."""
        stock_inicial = self.prod_stock_5.stock
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': 3}
        self.client_a.post(self.url_carro, payload, format='json')

        self.prod_stock_5.refresh_from_db()
        self.assertEqual(self.prod_stock_5.stock, stock_inicial)

    def test_05_agregar_mismo_producto_incrementa_cantidad(self):
        """5. Agregar un producto ya presente en el carro incrementa la cantidad existente."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        response = self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 4)
        item = response.data['items'][0]
        self.assertEqual(item['cantidad'], 4)

    def test_06_no_se_duplican_filas_carrito_item(self):
        """6. Reincorporar el mismo producto no genera registros duplicados en CarritoItem."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 1}, format='json')
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')

        items_count = CarritoItem.objects.filter(
            carrito__usuario=self.cliente_a,
            producto=self.prod_stock_5
        ).count()
        self.assertEqual(items_count, 1)

    # --------------------------------------------------------------------------
    # 3. VALIDACIONES DE ENTRADA Y STOCK
    # --------------------------------------------------------------------------
    def test_07_cantidad_0_produce_400(self):
        """7. Intentar agregar cantidad=0 es rechazado con HTTP 400."""
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': 0}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_08_cantidad_negativa_produce_400(self):
        """8. Intentar agregar cantidad negativa es rechazado con HTTP 400."""
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': -3}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_09_cantidad_mayor_al_stock_produce_400(self):
        """9. Solicitar una cantidad superior al stock físico total disponible retorna HTTP 400."""
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': 6}  # Stock es 5
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Stock insuficiente', str(response.data))

    def test_10_acumulacion_que_supera_stock_produce_400(self):
        """10. Incrementar unidades hasta superar el stock disponible es rechazado con HTTP 400."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 3}, format='json')
        # Ya tiene 3, si pide 3 más suma 6 > stock(5)
        response = self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Stock insuficiente', str(response.data))

    def test_11_producto_agotado_produce_400(self):
        """11. Intentar agregar un producto con stock=0 es rechazado con HTTP 400."""
        payload = {'producto_id': self.prod_agotado.id, 'cantidad': 1}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('agotado', str(response.data).lower())

    def test_12_producto_inactivo_produce_400(self):
        """12. Intentar agregar un producto inactivo (activo=False) es rechazado con HTTP 400."""
        payload = {'producto_id': self.prod_inactivo.id, 'cantidad': 1}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no está disponible', str(response.data).lower())

    # --------------------------------------------------------------------------
    # 4. ELIMINAR Y ACTUALIZAR ÍTEMS
    # --------------------------------------------------------------------------
    def test_13_delete_elimina_item(self):
        """13. DELETE /api/carro/{producto_id}/ elimina el ítem correspondiente del carro."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        url_item = reverse('api-carro-item', kwargs={'producto_id': self.prod_stock_5.id})

        response = self.client_a.delete(url_item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertFalse(CarritoItem.objects.filter(carrito__usuario=self.cliente_a).exists())

    def test_14_delete_no_modifica_stock(self):
        """14. Eliminar un producto del carro NO altera el stock físico del catálogo."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        stock_antes = self.prod_stock_5.stock

        url_item = reverse('api-carro-item', kwargs={'producto_id': self.prod_stock_5.id})
        self.client_a.delete(url_item)

        self.prod_stock_5.refresh_from_db()
        self.assertEqual(self.prod_stock_5.stock, stock_antes)

    def test_15_patch_modifica_cantidad(self):
        """15. PATCH /api/carro/{producto_id}/ actualiza la cantidad solicitada con éxito."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_10.id, 'cantidad': 2}, format='json')
        url_item = reverse('api-carro-item', kwargs={'producto_id': self.prod_stock_10.id})

        response = self.client_a.patch(url_item, {'cantidad': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 5)
        self.assertEqual(Decimal(str(response.data['total'])), Decimal('1950000.00'))

    def test_16_patch_sobre_stock_produce_400(self):
        """16. PATCH solicitando una cantidad que excede el stock físico retorna HTTP 400."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        url_item = reverse('api-carro-item', kwargs={'producto_id': self.prod_stock_5.id})

        response = self.client_a.patch(url_item, {'cantidad': 99}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Stock insuficiente', str(response.data))

    # --------------------------------------------------------------------------
    # 5. PERSISTENCIA Y AISLAMIENTO IDOR
    # --------------------------------------------------------------------------
    def test_17_carro_persiste_tras_logout_login(self):
        """17. El carro de compras persiste íntegro tras logout y nuevo login en base de datos."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 3}, format='json')

        # Simular nueva sesión / nuevo cliente HTTP autenticado con el mismo usuario
        nuevo_client = APIClient()
        nuevo_client.force_authenticate(user=self.cliente_a)

        response = nuevo_client.get(self.url_carro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)
        self.assertEqual(response.data['items'][0]['producto_id'], self.prod_stock_5.id)

    def test_18_segundo_usuario_tiene_carro_independiente(self):
        """18. Dos clientes distintos poseen carros estrictamente aislados e independientes."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        self.client_b.post(self.url_carro, {'producto_id': self.prod_stock_10.id, 'cantidad': 1}, format='json')

        res_a = self.client_a.get(self.url_carro)
        res_b = self.client_b.get(self.url_carro)

        self.assertEqual(res_a.data['total_items'], 2)
        self.assertEqual(res_a.data['items'][0]['producto_id'], self.prod_stock_5.id)

        self.assertEqual(res_b.data['total_items'], 1)
        self.assertEqual(res_b.data['items'][0]['producto_id'], self.prod_stock_10.id)

    def test_19_cliente_a_no_afecta_carro_cliente_b(self):
        """19. Control IDOR: Cliente A no puede eliminar ni modificar productos del carro de Cliente B."""
        # Cliente B tiene producto en su carro
        self.client_b.post(self.url_carro, {'producto_id': self.prod_stock_10.id, 'cantidad': 3}, format='json')

        # Cliente A intenta eliminar el producto del carro (que él no tiene agregado)
        url_item_b = reverse('api-carro-item', kwargs={'producto_id': self.prod_stock_10.id})
        res_del = self.client_a.delete(url_item_b)
        self.assertEqual(res_del.status_code, status.HTTP_404_NOT_FOUND)

        # El carro de B debe permanecer intacto con sus 3 unidades
        res_b = self.client_b.get(self.url_carro)
        self.assertEqual(res_b.data['total_items'], 3)

    # --------------------------------------------------------------------------
    # 6. PERMISOS Y ROLES
    # --------------------------------------------------------------------------
    def test_20_anonimo_get_carrito_produce_401(self):
        """20. Usuario anónimo recibe HTTP 401 Unauthorized al consultar /api/carro/."""
        response = self.client_anon.get(self.url_carro)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_21_anonimo_post_carrito_produce_401(self):
        """21. Usuario anónimo recibe HTTP 401 Unauthorized al intentar agregar productos."""
        payload = {'producto_id': self.prod_stock_5.id, 'cantidad': 1}
        response = self.client_anon.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_22_administrador_produce_403_segun_is_cliente_role(self):
        """22. Usuario con rol ADMINISTRADOR recibe HTTP 403 Forbidden según IsClienteRole."""
        res_get = self.client_admin.get(self.url_carro)
        self.assertEqual(res_get.status_code, status.HTTP_403_FORBIDDEN)

        res_post = self.client_admin.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 1})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    # --------------------------------------------------------------------------
    # 7. INTEGRACIÓN WEB (DJANGO SESSIONS & TEMPLATES)
    # --------------------------------------------------------------------------
    def test_23_contador_header_refleja_cantidad_real(self):
        """23. El contador del header renderiza la suma real de unidades para el cliente autenticado."""
        # 1. Sin productos: contador en 0
        response = self.web_client_a.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="header-cart-count">0<')

        # 2. Con productos: suma de cantidades
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_10.id, 'cantidad': 3}, format='json')

        response = self.web_client_a.get(reverse('home'))
        self.assertContains(response, 'id="header-cart-count">5<')

    def test_24_boton_web_agrega_producto(self):
        """24. Formulario web POST /carro/agregar/{id}/ agrega producto y redirige al detalle del carro."""
        url_add = reverse('carro_agregar', kwargs={'producto_id': self.prod_stock_5.id})
        response = self.web_client_a.post(url_add, {'cantidad': 2}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ryzen 7 7800X3D')
        self.assertContains(response, '840000')

    def test_25_pagina_carro_muestra_productos(self):
        """25. Vista /carro/ renderiza lista de productos, subtotales y total general."""
        self.client_a.post(self.url_carro, {'producto_id': self.prod_stock_5.id, 'cantidad': 2}, format='json')
        url_detalle = reverse('carro_detalle')
        response = self.web_client_a.get(url_detalle)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carro/detalle.html')
        self.assertContains(response, self.prod_stock_5.nombre)
        self.assertContains(response, self.prod_stock_5.sku)
        self.assertContains(response, 'Total a Pagar:')

    def test_26_producto_inexistente_produce_error_limpio(self):
        """26. Intentar agregar un producto inexistente produce error 404 JSON estructurado."""
        payload = {'producto_id': 99999, 'cantidad': 1}
        response = self.client_a.post(self.url_carro, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('status'), 404)
        self.assertIn('recurso no encontrado', response.data.get('error', '').lower())
