"""
Django settings for pupefactory project.

Evaluación EVA-2 Backend - Grupo 1: Tienda de Hardware y Componentes PC (PupeFactory)
Arquitectura limpia con Django + Django REST Framework + PostgreSQL.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga de variables de entorno desde .env
load_dotenv(BASE_DIR / '.env')

# ==============================================================================
# CONFIGURACIÓN BÁSICA Y SEGURIDAD
# ==============================================================================
SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]
if DEBUG and 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# ==============================================================================
# MODELO DE USUARIO PERSONALIZADO (DEFINIDO ANTES DE MIGRAR)
# ==============================================================================
AUTH_USER_MODEL = 'usuarios.CustomUser'

# ==============================================================================
# APLICACIONES INSTALADAS
# ==============================================================================
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías de terceros obligatorias
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',

    # Módulos del proyecto (Apps modulares)
    'apps.usuarios',
    'apps.catalogo',
    'apps.carro',
    'apps.ordenes',
    'apps.core',
]

# ==============================================================================
# MIDDLEWARE
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pupefactory.urls'

# ==============================================================================
# CONFIGURACIÓN DE TEMPLATES Y CONTEXT PROCESSORS
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Context processor obligatorio con los datos del alumno en footer
                'apps.core.context_processors.footer_context',
                # Context processor con contador dinámico del carro de compras
                'apps.carro.context_processors.carro_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'pupefactory.wsgi.application'

# ==============================================================================
# BASE DE DATOS: CONFIGURACIÓN NATIVA CON POSTGRESQL (CON SOPORTE SQLITE LOCAL)
# ==============================================================================
DB_ENGINE = os.environ.get('DB_ENGINE', 'postgresql').lower()

if DB_ENGINE in ('sqlite', 'sqlite3'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'pupefactory_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# INTERNACIONALIZACIÓN Y ZONA HORARIA
# ==============================================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# ==============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# DJANGO REST FRAMEWORK (DRF)
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# ==============================================================================
# SIMPLE JWT (AUTENTICACIÓN BASADA EN TOKENS)
# ==============================================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ==============================================================================
# DRF SPECTACULAR (OPENAPI 3.0 / SWAGGER)
# ==============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'PupeFactory API - Hardware & Componentes PC',
    'DESCRIPTION': 'Documentación privada de la API REST para PupeFactory (EVA-2 Backend). Acceso restringido a administradores.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'SECURITY': [{'BearerAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
}

# ==============================================================================
# DATOS DEL ESTUDIANTE (REQUERIMIENTO RÚBRICA - FOOTER)
# ==============================================================================
ALUMNO_NOMBRE = os.environ.get('ALUMNO_NOMBRE', 'Nombre Alumno')
ALUMNO_SECCION = os.environ.get('ALUMNO_SECCION', 'Sección 1')
ALUMNO_ANIO = os.environ.get('ALUMNO_ANIO', '2026')

# ==============================================================================
# REDIRECCIONES DE AUTENTICACIÓN WEB
# ==============================================================================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

