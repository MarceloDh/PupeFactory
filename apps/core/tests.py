from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse


class CoreAuditTestCase(TestCase):
    """
    Pruebas para requerimientos de auditoría Fase 3.6 (Core):
    - 404 Web retorna HTML personalizado
    - 404 API retorna JSON con estructura de error estándar
    - Footer renderiza las variables de contexto del alumno
    """

    def setUp(self):
        self.client = Client()

    def test_01_ruta_inexistente_web_retorna_404_html(self):
        """1. /FRgregreghre retorna HTTP 404 con plantilla errors/404.html."""
        response = self.client.get('/FRgregreghre')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')
        self.assertIn('text/html', response['Content-Type'])
        self.assertContains(response, 'Página no encontrada', status_code=404)

    def test_02_ruta_inexistente_api_retorna_404_json(self):
        """2. /api/FRgregreghre/ retorna HTTP 404 en JSON sin HTML ni trazas."""
        response = self.client.get('/api/FRgregreghre/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data.get('status'), 404)
        self.assertEqual(data.get('error'), 'Recurso no encontrado.')

    def test_15_footer_contiene_datos_del_alumno(self):
        """15. El footer en las vistas base renderiza el nombre, sección y año del alumno."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        # Verificar que se inyectan y muestran los datos del alumno entregados por footer_context
        alumno_nombre = getattr(settings, 'ALUMNO_NOMBRE', 'Estudiante')
        alumno_seccion = getattr(settings, 'ALUMNO_SECCION', 'Sección')
        alumno_anio = getattr(settings, 'ALUMNO_ANIO', '2026')

        self.assertContains(response, alumno_nombre)
        self.assertContains(response, alumno_seccion)
        self.assertContains(response, alumno_anio)
        self.assertContains(response, 'PupeFactory')
