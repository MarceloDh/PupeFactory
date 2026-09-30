from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from apps.usuarios.serializers import CustomTokenObtainPairSerializer

# ==============================================================================
# VISTAS DE AUTENTICACIÓN API (JWT)
# ==============================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint POST /api/auth/token/
    Recibe username y password, devuelve access y refresh tokens
    con los claims personalizados de user_id, username y role.
    """
    serializer_class = CustomTokenObtainPairSerializer


# ==============================================================================
# VISTAS DE AUTENTICACIÓN WEB (SESIONES DJANGO TEMPLATES)
# ==============================================================================

class UsuarioLoginView(LoginView):
    """
    Vista de inicio de sesión web tradicional mediante Django Sessions.
    Utiliza el mismo modelo CustomUser que la API REST.
    Redirige a LOGIN_REDIRECT_URL ('/') tras éxito.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Credenciales incorrectas. Verifique su usuario y contraseña.")
        return super().form_invalid(form)


class UsuarioLogoutView(LogoutView):
    """
    Vista de cierre de sesión web tradicional.
    Elimina la sesión del usuario en la base de datos de PostgreSQL.
    """
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado sesión correctamente.")
        return super().dispatch(request, *args, **kwargs)
