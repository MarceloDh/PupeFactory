from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.usuarios.views import (
    CustomTokenObtainPairView,
    UsuarioLoginView,
    UsuarioLogoutView,
)

urlpatterns = [
    # Endpoints de Autenticación API (JWT)
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Rutas de Autenticación Web (Django Templates / Sesión)
    path('accounts/login/', UsuarioLoginView.as_view(), name='login'),
    path('accounts/logout/', UsuarioLogoutView.as_view(), name='logout'),
]
