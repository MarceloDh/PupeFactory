from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import UntypedToken
import jwt
from django.conf import settings
from apps.usuarios.models import CustomUser

# ==============================================================================
# SUITE DE PRUEBAS AUTOMATIZADAS - FASE 2: AUTENTICACIÓN, ROLES Y SWAGGER
# ==============================================================================
# Cubre exhaustivamente los 10 casos obligatorios solicitados:
# - JWT login y generación de tokens
# - Claims en payload (user_id, username, role)
# - Refresh token
# - Protección de Swagger y OpenAPI Schema por rol en backend
# - Login y Logout tradicional por sesiones Django
# ==============================================================================

class AutenticacionYPermisosTestCase(TestCase):

    def setUp(self):
        # Crear usuario Cliente
        self.cliente = CustomUser.objects.create_user(
            username='cliente_test',
            email='cliente@pupefactory.cl',
            password='Password123!',
            role=CustomUser.Role.CLIENTE
        )

        # Crear usuario Administrador
        self.admin = CustomUser.objects.create_user(
            username='admin_test',
            email='admin@pupefactory.cl',
            password='AdminPassword123!',
            role=CustomUser.Role.ADMINISTRADOR,
            is_staff=True
        )

        self.api_client = APIClient()
        self.web_client = Client()

    def test_caso_1_jwt_login_credenciales_correctas(self):
        """CASO 1: POST /api/auth/token/ con credenciales de cliente retorna 200, access y refresh."""
        url = reverse('token_obtain_pair')
        response = self.api_client.post(url, {
            'username': 'cliente_test',
            'password': 'Password123!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], CustomUser.Role.CLIENTE)

    def test_caso_2_jwt_payload_incluye_claims_de_rol(self):
        """CASO 2: Decodificar token cliente y verificar claims obligatorios: user_id, username, role."""
        url = reverse('token_obtain_pair')
        response = self.api_client.post(url, {
            'username': 'cliente_test',
            'password': 'Password123!'
        }, format='json')

        access_token = response.data['access']
        # Decodificar el token sin verificar firma para inspeccionar claims
        decoded_payload = jwt.decode(access_token, options={"verify_signature": False})

        self.assertEqual(decoded_payload['user_id'], self.cliente.id)
        self.assertEqual(decoded_payload['username'], 'cliente_test')
        self.assertEqual(decoded_payload['role'], CustomUser.Role.CLIENTE)

    def test_caso_3_jwt_refresh_token(self):
        """CASO 3: POST /api/auth/token/refresh/ genera un nuevo access token válido."""
        token_url = reverse('token_obtain_pair')
        login_res = self.api_client.post(token_url, {
            'username': 'cliente_test',
            'password': 'Password123!'
        }, format='json')
        refresh_token = login_res.data['refresh']

        refresh_url = reverse('token_refresh')
        response = self.api_client.post(refresh_url, {
            'refresh': refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_caso_4_cliente_intenta_ver_swagger_docs(self):
        """CASO 4: Un cliente autenticado intenta entrar a /api/docs/ -> 403 Forbidden."""
        self.web_client.login(username='cliente_test', password='Password123!')
        response = self.web_client.get('/api/docs/')

        # Debe ser rechazado por backend con 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_caso_5_cliente_intenta_ver_schema_openapi(self):
        """CASO 5: Un cliente intenta consultar /api/schema/ -> 403 Forbidden."""
        self.web_client.login(username='cliente_test', password='Password123!')
        response = self.web_client.get('/api/schema/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_caso_6_admin_visita_swagger_docs(self):
        """CASO 6: Un administrador autenticado visita /api/docs/ -> 200 OK con Swagger UI."""
        self.web_client.login(username='admin_test', password='AdminPassword123!')
        response = self.web_client.get('/api/docs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'swagger-ui')

    def test_caso_7_admin_visita_schema_openapi(self):
        """CASO 7: Un administrador visita /api/schema/ -> 200 OK con esquema OpenAPI."""
        self.web_client.login(username='admin_test', password='AdminPassword123!')
        response = self.web_client.get('/api/schema/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_caso_8_anonimo_visita_documentacion(self):
        """CASO 8: Usuario anónimo no autenticado visita Swagger o Schema -> Denegado (401 o 403)."""
        response_docs = self.web_client.get('/api/docs/')
        self.assertIn(response_docs.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        response_schema = self.web_client.get('/api/schema/')
        self.assertIn(response_schema.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_caso_9_login_html_cliente(self):
        """CASO 9: Login HTML tradicional crea la sesión web y autentica a request.user."""
        response = self.web_client.post(reverse('login'), {
            'username': 'cliente_test',
            'password': 'Password123!'
        }, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que el usuario quedó autenticado en la sesión mediante request.user
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.role, CustomUser.Role.CLIENTE)

    def test_caso_10_logout_html(self):
        """CASO 10: Logout HTML tradicional termina la sesión de forma limpia."""
        self.web_client.login(username='cliente_test', password='Password123!')
        response = self.web_client.post(reverse('logout'), follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_credenciales_invalidas_retornan_401_limpio(self):
        """Prueba adicional: Credenciales erróneas en JWT retornan 401 sin exponer trazas técnicas."""
        url = reverse('token_obtain_pair')
        response = self.api_client.post(url, {
            'username': 'cliente_test',
            'password': 'PasswordEquivocada!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 401)
