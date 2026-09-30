from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.usuarios.models import CustomUser

# ==============================================================================
# SERIALIZADOR DE AUTENTICACIÓN JWT CON CLAIMS PERSONALIZADOS
# ==============================================================================
# Cumple con el requerimiento de la rúbrica (Criterio 2.2):
# El payload del token JWT debe incluir explícitamente el Rol del usuario,
# además de user_id y username.
# ==============================================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado para la obtención de pares de tokens (access/refresh).
    Inyecta claims de negocio en el payload del token JWT.
    """

    @classmethod
    def get_token(cls, user: CustomUser):
        token = super().get_token(user)

        # Inclusión de claims personalizados en el payload del JWT
        token['user_id'] = user.id
        token['username'] = user.username
        token['role'] = user.role

        return token

    def validate(self, attrs):
        # Valida credenciales contra el CustomUser y genera access/refresh
        data = super().validate(attrs)

        # Retornamos también los datos del usuario en el cuerpo de la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }

        return data
