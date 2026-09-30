from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.catalogo.models import Categoria, Marca, Producto

# ==============================================================================
# COMANDO PARA POBLAR CATÁLOGO CON IMÁGENES REALES (SOLO DEBUG=True)
# ==============================================================================
# Configura categorías, marcas y los 8 componentes con imágenes reales locales y URLs oficiales.
# ==============================================================================

class Command(BaseCommand):
    help = 'Puebla el catálogo de demostración con imágenes oficiales y reales de hardware.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Operación bloqueada: Solo permitido en modo desarrollo (DEBUG=True).")

        # 1. Categorías
        categorias_data = [
            ('Procesadores', 'procesadores', 'CPUs Intel y AMD para gaming y productividad.'),
            ('Tarjetas de Video', 'tarjetas-video', 'GPUs NVIDIA GeForce y AMD Radeon de última generación.'),
            ('Memorias RAM', 'memorias-ram', 'Módulos DDR4 y DDR5 de alta frecuencia.'),
            ('Almacenamiento', 'almacenamiento', 'Unidades SSD NVMe M.2 y discos de alta velocidad.'),
            ('Placas Madre', 'placas-madre', 'Motherboards para plataformas AM5 y LGA1700.'),
        ]
        cat_objs = {}
        for nombre, slug, desc in categorias_data:
            cat, _ = Categoria.objects.get_or_create(slug=slug, defaults={'nombre': nombre, 'descripcion': desc})
            cat_objs[slug] = cat

        # 2. Marcas
        marcas_data = [
            ('AMD', 'amd'),
            ('NVIDIA', 'nvidia'),
            ('ASUS', 'asus'),
            ('MSI', 'msi'),
            ('Corsair', 'corsair'),
            ('Kingston', 'kingston'),
        ]
        marca_objs = {}
        for nombre, slug in marcas_data:
            m, _ = Marca.objects.get_or_create(slug=slug, defaults={'nombre': nombre})
            marca_objs[slug] = m

        # 3. Productos con imágenes locales y URLs oficiales
        productos_data = [
            {
                'nombre': 'AMD Ryzen 7 7800X3D',
                'sku': 'CPU-AMD-7800X3D',
                'categoria': cat_objs['procesadores'],
                'marca': marca_objs['amd'],
                'descripcion': 'El procesador definitivo para gaming. 8 núcleos, 16 hilos y tecnología 3D V-Cache.',
                'precio': Decimal('429990.00'),
                'stock': 8,
                'activo': True,
                'imagen': 'productos/ryzen_7800x3d.jpg',
                'imagen_url': 'https://www.amd.com/content/dam/amd/en/images/products/processors/ryzen/2505503-ryzen-7-7800x3d-front.jpg'
            },
            {
                'nombre': 'AMD Ryzen 5 7600X',
                'sku': 'CPU-AMD-7600X',
                'categoria': cat_objs['procesadores'],
                'marca': marca_objs['amd'],
                'descripcion': 'Excelente rendimiento para gaming y multitarea. 6 núcleos y 12 hilos hasta 5.3 GHz.',
                'precio': Decimal('229990.00'),
                'stock': 14,
                'activo': True,
                'imagen': 'productos/ryzen_7600x.jpg',
                'imagen_url': 'https://www.amd.com/content/dam/amd/en/images/products/processors/ryzen/2505503-ryzen-5-7600x.jpg'
            },
            {
                'nombre': 'ASUS ROG Strix GeForce RTX 5070 16GB',
                'sku': 'GPU-ASUS-RTX5070-16G',
                'categoria': cat_objs['tarjetas-video'],
                'marca': marca_objs['asus'],
                'descripcion': 'Arquitectura de nueva generación con triple ventilador axial y trazado de rayos avanzado.',
                'precio': Decimal('789990.00'),
                'stock': 4,
                'activo': True,
                'imagen': 'productos/asus_rtx5070.png',
                'imagen_url': 'https://dlcdnwebimgs.asus.com/files/media/d48133b3-efb2-4e3f-9eed-51959e89f74c/v1/img/kv/pd.png'
            },
            {
                'nombre': 'MSI GeForce RTX 4060 Ventus 2X 8GB',
                'sku': 'GPU-MSI-RTX4060-8G',
                'categoria': cat_objs['tarjetas-video'],
                'marca': marca_objs['msi'],
                'descripcion': 'Eficiencia energética y tecnología DLSS 3 para jugar a 1080p con máximos detalles.',
                'precio': Decimal('339990.00'),
                'stock': 12,
                'activo': True,
                'imagen': 'productos/msi_rtx4060.png',
                'imagen_url': 'https://storage-asset.msi.com/global/picture/image/feature/vga/NVIDIA/RTX-4060-VENTUS-2X-BLACK-8G/images/msi-rtx4060-ventus-2x-black-8g-kv.png'
            },
            {
                'nombre': 'Corsair Vengeance RGB DDR5 32GB (2x16GB) 6000MHz',
                'sku': 'RAM-COR-DDR5-32G6000',
                'categoria': cat_objs['memorias-ram'],
                'marca': marca_objs['corsair'],
                'descripcion': 'Kit de memoria DDR5 de alto rendimiento optimizado para AMD EXPO e Intel XMP.',
                'precio': Decimal('134990.00'),
                'stock': 20,
                'activo': True,
                'imagen': 'productos/corsair_ddr5.webp',
                'imagen_url': 'https://assets.corsair.com/image/upload/c_pad,q_auto,h_1024,w_1024,f_auto/products/Memory/vengeance-rgb-ddr5-blk-config/Gallery/2up/VENGEANCE_RGB_DDR5_BLK_01.webp'
            },
            {
                'nombre': 'Kingston Fury Beast DDR4 16GB (2x8GB) 3200MHz',
                'sku': 'RAM-KIN-DDR4-16G3200',
                'categoria': cat_objs['memorias-ram'],
                'marca': marca_objs['kingston'],
                'descripcion': 'Memoria confiable y veloz para plataformas DDR4. Producto temporalmente agotado.',
                'precio': Decimal('42990.00'),
                'stock': 0,  # AGOTADO para probar filtro de disponibilidad
                'activo': True,
                'imagen': 'productos/kingston_fury_beast.jpg',
                'imagen_url': 'https://media.kingston.com/kingston/press/ktc-press-fury-renegade-beast-ddr4-lg.jpg'
            },
            {
                'nombre': 'Kingston KC3000 2TB NVMe PCIe 4.0 M.2',
                'sku': 'SSD-KIN-KC3000-2TB',
                'categoria': cat_objs['almacenamiento'],
                'marca': marca_objs['kingston'],
                'descripcion': 'Velocidades extremas de lectura/escritura de hasta 7000 MB/s con controlador Phison E18.',
                'precio': Decimal('164990.00'),
                'stock': 9,
                'activo': True,
                'imagen': 'productos/kingston_kc3000.jpg',
                'imagen_url': 'https://tpucdn.com/ssd-specs/images/d/260-front.jpg'
            },
            {
                'nombre': 'ASUS TUF Gaming B650-PLUS WIFI',
                'sku': 'MB-ASUS-TUF-B650P',
                'categoria': cat_objs['placas-madre'],
                'marca': marca_objs['asus'],
                'descripcion': 'Placa madre Socket AM5 con diseño militar duradero, PCIe 5.0 M.2 y WiFi 6 integrado.',
                'precio': Decimal('199990.00'),
                'stock': 6,
                'activo': True,
                'imagen': 'productos/asus_tuf_b650.png',
                'imagen_url': 'https://dlcdnwebimgs.asus.com/files/media/7f358aac-d2d6-4dd0-8fba-dea85469a22e/V1/img/kv-main.png'
            },
        ]

        count = 0
        for pdata in productos_data:
            sku = pdata['sku']
            p, created = Producto.objects.update_or_create(sku=sku, defaults=pdata)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] Catálogo actualizado con {count} productos e imágenes reales."))
