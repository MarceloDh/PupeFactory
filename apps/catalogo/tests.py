from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from apps.catalogo.models import Categoria, Marca, Producto
from apps.usuarios.models import CustomUser

# ==============================================================================
# SUITE DE PRUEBAS AUTOMATIZADAS - FASE 3: CATÁLOGO, FILTROS Y CRUD
# ==============================================================================
# Cubre exhaustivamente los 20 casos obligatorios solicitados:
# - Permisos públicos vs cliente vs administrador
# - CRUD de productos
# - Baja lógica (soft-delete con activo=False)
# - Filtros avanzados de django-filter (categoría, marca, precios, disponibilidad)
# - Búsqueda por texto con SearchFilter (nombre, SKU, marca)
# - Validaciones de negocio (precio, stock, SKU) y manejo limpio de 404
# ==============================================================================

class CatalogoTestCase(TestCase):

    def setUp(self):
        # Crear Categorías
        self.cat_cpu = Categoria.objects.create(nombre='Procesadores', slug='procesadores')
        self.cat_gpu = Categoria.objects.create(nombre='Tarjetas de Video', slug='tarjetas-video')

        # Crear Marcas
        self.marca_amd = Marca.objects.create(nombre='AMD', slug='amd')
        self.marca_nvidia = Marca.objects.create(nombre='NVIDIA', slug='nvidia')
        self.marca_asus = Marca.objects.create(nombre='ASUS', slug='asus')

        # Crear Productos de prueba
        self.prod_ryzen = Producto.objects.create(
            nombre='Ryzen 7 7800X3D',
            sku='CPU-AMD-7800X3D',
            categoria=self.cat_cpu,
            marca=self.marca_amd,
            descripcion='Procesador para gaming de alto rendimiento',
            precio=Decimal('420000.00'),
            stock=10,
            activo=True
        )

        self.prod_rtx = Producto.objects.create(
            nombre='GeForce RTX 5070',
            sku='GPU-NV-5070-ASUS',
            categoria=self.cat_gpu,
            marca=self.marca_asus,
            descripcion='Tarjeta gráfica de última generación',
            precio=Decimal('750000.00'),
            stock=5,
            activo=True
        )

        self.prod_agotado = Producto.objects.create(
            nombre='Ryzen 5 5600',
            sku='CPU-AMD-5600',
            categoria=self.cat_cpu,
            marca=self.marca_amd,
            descripcion='Procesador gama media',
            precio=Decimal('130000.00'),
            stock=0,  # Sin stock
            activo=True
        )

        self.prod_inactivo = Producto.objects.create(
            nombre='Producto Antiguo Descontinuado',
            sku='OLD-CPU-001',
            categoria=self.cat_cpu,
            marca=self.marca_amd,
            descripcion='No disponible públicamente',
            precio=Decimal('50000.00'),
            stock=2,
            activo=False  # Desactivado
        )

        # Usuarios
        self.cliente = CustomUser.objects.create_user(
            username='cliente_test',
            password='Password123!',
            role=CustomUser.Role.CLIENTE
        )

        self.admin = CustomUser.objects.create_user(
            username='admin_test',
            password='AdminPassword123!',
            role=CustomUser.Role.ADMINISTRADOR,
            is_staff=True
        )

        self.client_anon = APIClient()

        self.client_cliente = APIClient()
        self.client_cliente.force_authenticate(user=self.cliente)

        self.client_admin = APIClient()
        self.client_admin.force_authenticate(user=self.admin)

    # --------------------------------------------------------------------------
    # 1. PÚBLICO Y ACCESO DE LECTURA
    # --------------------------------------------------------------------------
    def test_01_publico_lista_productos(self):
        """1. Público lista productos activos exitosamente."""
        url = reverse('producto-list')
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo deben figurar los 3 productos activos
        self.assertEqual(len(response.data), 3)

    def test_02_publico_ve_producto_individual(self):
        """2. Público ve detalle de un producto activo individual."""
        url = reverse('producto-detail', kwargs={'pk': self.prod_ryzen.pk})
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Ryzen 7 7800X3D')
        self.assertEqual(response.data['disponible'], True)

    def test_03_publico_no_puede_crear_producto(self):
        """3. Público anónimo no puede crear productos (HTTP 401)."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Nuevo Item',
            'sku': 'SKU-NUEVO-001',
            'categoria': self.cat_cpu.id,
            'marca': self.marca_amd.id,
            'precio': '150000.00',
            'stock': 4
        }
        response = self.client_anon.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_04_cliente_no_puede_crear_producto(self):
        """4. Cliente autenticado no puede crear productos (HTTP 403)."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Nuevo Item Cliente',
            'sku': 'SKU-CLI-001',
            'categoria': self.cat_cpu.id,
            'marca': self.marca_amd.id,
            'precio': '150000.00',
            'stock': 4
        }
        response = self.client_cliente.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --------------------------------------------------------------------------
    # 2. OPERACIONES ADMINISTRATIVAS (CRUD + BAJA LÓGICA)
    # --------------------------------------------------------------------------
    def test_05_admin_puede_crear_producto(self):
        """5. Administrador puede crear producto exitosamente (HTTP 201)."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Core i7 14700K',
            'sku': 'CPU-INTEL-14700K',
            'categoria': self.cat_cpu.id,
            'marca': self.marca_asus.id,
            'descripcion': 'Procesador Intel LGA1700',
            'precio': '390000.00',
            'stock': 8
        }
        response = self.client_admin.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Producto.objects.filter(sku='CPU-INTEL-14700K').exists())

    def test_06_admin_puede_modificar_producto(self):
        """6. Administrador puede modificar producto existente con PATCH (HTTP 200)."""
        url = reverse('producto-detail', kwargs={'pk': self.prod_ryzen.pk})
        data = {'precio': '410000.00', 'stock': 15}
        response = self.client_admin.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.prod_ryzen.refresh_from_db()
        self.assertEqual(self.prod_ryzen.precio, Decimal('410000.00'))
        self.assertEqual(self.prod_ryzen.stock, 15)

    def test_07_delete_administrativo_realiza_baja_logica(self):
        """7. DELETE administrativo desactiva el producto (activo=False) en lugar de borrar la fila."""
        url = reverse('producto-detail', kwargs={'pk': self.prod_rtx.pk})
        response = self.client_admin.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la fila sigue existiendo en PostgreSQL con activo=False
        self.prod_rtx.refresh_from_db()
        self.assertFalse(self.prod_rtx.activo)

    def test_08_producto_desactivado_desaparece_del_catalogo_publico(self):
        """8. Producto desactivado desaparece del listado público y detalle público."""
        # Desactivar prod_ryzen
        self.prod_ryzen.activo = False
        self.prod_ryzen.save()

        # En listado público ya no debe figurar
        url_list = reverse('producto-list')
        res_list = self.client_anon.get(url_list)
        skus_en_lista = [p['sku'] for p in res_list.data]
        self.assertNotIn(self.prod_ryzen.sku, skus_en_lista)

        # En detalle público debe retornar 404
        url_detail = reverse('producto-detail', kwargs={'pk': self.prod_ryzen.pk})
        res_detail = self.client_anon.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

    # --------------------------------------------------------------------------
    # 3. FILTROS AVANZADOS (DJANGO-FILTER)
    # --------------------------------------------------------------------------
    def test_09_filtro_categoria_funciona(self):
        """9. Filtrar por categoría (?categoria=tarjetas-video) retorna solo productos de esa categoría."""
        url = f"{reverse('producto-list')}?categoria=tarjetas-video"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], self.prod_rtx.sku)

    def test_10_filtro_marca_funciona(self):
        """10. Filtrar por marca (?marca=asus) retorna solo productos de ASUS."""
        url = f"{reverse('producto-list')}?marca=asus"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], self.prod_rtx.sku)

    def test_11_filtro_precio_min_funciona(self):
        """11. Filtrar por precio_min (?precio_min=400000) retorna productos con precio >= 400.000."""
        url = f"{reverse('producto-list')}?precio_min=400000"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Deben calificar: Ryzen 7 (420.000) y RTX 5070 (750.000)
        self.assertEqual(len(response.data), 2)

    def test_12_filtro_precio_max_funciona(self):
        """12. Filtrar por precio_max (?precio_max=200000) retorna productos con precio <= 200.000."""
        url = f"{reverse('producto-list')}?precio_max=200000"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo califica Ryzen 5 5600 (130.000)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], self.prod_agotado.sku)

    def test_13_filtro_disponibilidad_funciona(self):
        """13. Filtrar por disponibilidad (?disponible=true y ?disponible=false)."""
        # Con stock
        url_disp = f"{reverse('producto-list')}?disponible=true"
        res_disp = self.client_anon.get(url_disp)
        self.assertEqual(len(res_disp.data), 2)  # Ryzen 7 y RTX

        # Sin stock
        url_agot = f"{reverse('producto-list')}?disponible=false"
        res_agot = self.client_anon.get(url_agot)
        self.assertEqual(len(res_agot.data), 1)  # Ryzen 5
        self.assertEqual(res_agot.data[0]['sku'], self.prod_agotado.sku)

    # --------------------------------------------------------------------------
    # 4. BÚSQUEDA POR TEXTO (SEARCHFILTER)
    # --------------------------------------------------------------------------
    def test_14_busqueda_por_nombre_funciona(self):
        """14. Búsqueda (?search=Ryzen) retorna los productos cuyo nombre coincide."""
        url = f"{reverse('producto-list')}?search=Ryzen"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_15_busqueda_por_sku_funciona(self):
        """15. Búsqueda (?search=5070-ASUS) retorna el producto por su código SKU."""
        url = f"{reverse('producto-list')}?search=5070-ASUS"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], self.prod_rtx.sku)

    def test_16_busqueda_por_marca_funciona(self):
        """16. Búsqueda (?search=ASUS) retorna productos asociados a la marca ASUS."""
        url = f"{reverse('producto-list')}?search=ASUS"
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], self.prod_rtx.sku)

    # --------------------------------------------------------------------------
    # 5. VALIDACIONES Y MANEJO DE ERRORES
    # --------------------------------------------------------------------------
    def test_17_precio_invalido_produce_http_400(self):
        """17. Intentar crear un producto con precio <= 0 retorna HTTP 400 controlado."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Mouse Gaming',
            'sku': 'MOU-001',
            'categoria': self.cat_cpu.id,
            'marca': self.marca_amd.id,
            'precio': '0.00',  # Inválido
            'stock': 5
        }
        response = self.client_admin.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('precio', response.data['detalles'])

    def test_18_stock_negativo_produce_http_400(self):
        """18. Intentar crear o actualizar con stock negativo retorna HTTP 400 controlado."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Teclado Mecanico',
            'sku': 'KB-001',
            'categoria': self.cat_cpu.id,
            'marca': self.marca_amd.id,
            'precio': '45000.00',
            'stock': -3  # Inválido
        }
        response = self.client_admin.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock', response.data['detalles'])

    def test_19_sku_duplicado_produce_http_400(self):
        """19. Intentar registrar un producto con un SKU ya existente retorna HTTP 400."""
        url = reverse('producto-list')
        data = {
            'nombre': 'Otro Ryzen',
            'sku': self.prod_ryzen.sku,  # Duplicado
            'categoria': self.cat_cpu.id,
            'marca': self.marca_amd.id,
            'precio': '400000.00',
            'stock': 2
        }
        response = self.client_admin.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sku', response.data['detalles'])

    def test_20_producto_inexistente_produce_404_limpio(self):
        """20. Consultar un producto inexistente (/api/productos/99999/) retorna JSON 404 limpio."""
        url = reverse('producto-detail', kwargs={'pk': 99999})
        response = self.client_anon.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 404)
        self.assertEqual(response.data['error'], 'Recurso no encontrado.')

    # --------------------------------------------------------------------------
    # 7. AUDITORÍA FASE 3.6: FILTROS WEB, BÚSQUEDA Y CONTROL DE PROTECT
    # --------------------------------------------------------------------------
    def test_21_filtro_web_categoria_por_id(self):
        """21. Filtro web de categoría funciona con ID numérico (?categoria=1)."""
        url = reverse('catalogo')
        response = self.client.get(url, {'categoria': str(self.cat_cpu.id)})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertTrue(all(p.categoria_id == self.cat_cpu.id for p in prods))
        self.assertIn(self.prod_ryzen, prods)
        self.assertNotIn(self.prod_rtx, prods)

    def test_22_filtro_web_categoria_por_slug(self):
        """22. Filtro web de categoría funciona con slug (?categoria=procesadores)."""
        url = reverse('catalogo')
        response = self.client.get(url, {'categoria': 'procesadores'})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertTrue(all(p.categoria.slug == 'procesadores' for p in prods))
        self.assertIn(self.prod_ryzen, prods)
        self.assertNotIn(self.prod_rtx, prods)

    def test_23_filtro_web_marca_por_id(self):
        """23. Filtro web de marca funciona con ID numérico (?marca=2)."""
        url = reverse('catalogo')
        response = self.client.get(url, {'marca': str(self.marca_asus.id)})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertTrue(all(p.marca_id == self.marca_asus.id for p in prods))
        self.assertIn(self.prod_rtx, prods)
        self.assertNotIn(self.prod_ryzen, prods)

    def test_24_filtro_web_marca_por_slug(self):
        """24. Filtro web de marca funciona con slug (?marca=asus)."""
        url = reverse('catalogo')
        response = self.client.get(url, {'marca': 'asus'})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertTrue(all(p.marca.slug == 'asus' for p in prods))
        self.assertIn(self.prod_rtx, prods)
        self.assertNotIn(self.prod_ryzen, prods)

    def test_25_busqueda_web_por_marca(self):
        """25. Búsqueda web por nombre de marca (?q=ASUS) retorna productos de esa marca."""
        url = reverse('catalogo')
        response = self.client.get(url, {'q': 'ASUS'})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertIn(self.prod_rtx, prods)
        self.assertNotIn(self.prod_ryzen, prods)

    def test_26_busqueda_web_por_categoria(self):
        """26. Búsqueda web por nombre de categoría (?q=Procesadores) retorna productos de esa categoría."""
        url = reverse('catalogo')
        response = self.client.get(url, {'q': 'Procesadores'})
        self.assertEqual(response.status_code, 200)
        prods = list(response.context['productos'])
        self.assertIn(self.prod_ryzen, prods)
        self.assertNotIn(self.prod_rtx, prods)

    def test_27_admin_elimina_categoria_vacia(self):
        """27. Administrador puede eliminar una categoría sin productos asociados (HTTP 204)."""
        cat_vacia = Categoria.objects.create(nombre='Fuentes de Poder', slug='fuentes-poder')
        url = reverse('categoria-detail', kwargs={'pk': cat_vacia.pk})
        response = self.client_admin.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Categoria.objects.filter(pk=cat_vacia.pk).exists())

    def test_28_admin_no_elimina_categoria_usada(self):
        """28. Administrador recibe HTTP 409 Conflict si intenta eliminar categoría con productos asociados."""
        url = reverse('categoria-detail', kwargs={'pk': self.cat_cpu.pk})
        response = self.client_admin.delete(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data.get('status'), 409)
        self.assertIn('No se puede eliminar la categoría porque contiene productos asociados.', response.data.get('error', ''))
        self.assertTrue(Categoria.objects.filter(pk=self.cat_cpu.pk).exists())

    def test_29_admin_elimina_marca_vacia(self):
        """29. Administrador puede eliminar una marca sin productos asociados (HTTP 204)."""
        marca_vacia = Marca.objects.create(nombre='Corsair', slug='corsair')
        url = reverse('marca-detail', kwargs={'pk': marca_vacia.pk})
        response = self.client_admin.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Marca.objects.filter(pk=marca_vacia.pk).exists())

    def test_30_admin_no_elimina_marca_usada(self):
        """30. Administrador recibe HTTP 409 Conflict si intenta eliminar marca con productos asociados."""
        url = reverse('marca-detail', kwargs={'pk': self.marca_amd.pk})
        response = self.client_admin.delete(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data.get('status'), 409)
        self.assertIn('No se puede eliminar la marca porque contiene productos asociados.', response.data.get('error', ''))
        self.assertTrue(Marca.objects.filter(pk=self.marca_amd.pk).exists())

    def test_31_cliente_no_puede_eliminar_categoria(self):
        """31. Usuario con rol Cliente no tiene permisos para eliminar categorías (HTTP 403)."""
        cat_vacia = Categoria.objects.create(nombre='Periféricos', slug='perifericos')
        url = reverse('categoria-detail', kwargs={'pk': cat_vacia.pk})
        response = self.client_cliente.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Categoria.objects.filter(pk=cat_vacia.pk).exists())

    def test_32_cliente_no_puede_eliminar_marca(self):
        """32. Usuario con rol Cliente no tiene permisos para eliminar marcas (HTTP 403)."""
        marca_vacia = Marca.objects.create(nombre='Kingston', slug='kingston')
        url = reverse('marca-detail', kwargs={'pk': marca_vacia.pk})
        response = self.client_cliente.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Marca.objects.filter(pk=marca_vacia.pk).exists())

