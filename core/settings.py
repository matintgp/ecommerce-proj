import os
from pathlib import Path
from datetime import timedelta
from django.conf import settings
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-4@#)6&!$@^@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!'

DEBUG = True # TODO: yadam nare False konam

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps i installed
    'rest_framework',
    'drf_yasg',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    
    # Local apps
    'apps.accounts',
    'apps.orders',
    'apps.products',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'frontend',  # frontend files (one templat html)
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', 
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
AUTH_USER_MODEL = 'accounts.User'



# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'staticfiles'  
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



#  Django Rest Framework setings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "JWT Format: \"Bearer <token>\""
        }
    },
    'DEFAULT_MODEL_RENDERING': 'example',
    'USE_SESSION_AUTH': False,
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'AUTO_SCHEMA_TYPE_INSPECTORS': [
        'drf_yasg.inspectors.SwaggerAutoSchema',
        'drf_yasg.inspectors.CoreAPICompatInspector',
    ],
    'DEFAULT_AUTO_SCHEMA_CLASS': 'drf_yasg.inspectors.SwaggerAutoSchema',
    "DEFAULT_TAGS": []
}



# CSRF settings 
CSRF_COOKIE_SAMESITE = 'Lax'  
CSRF_COOKIE_HTTPONLY = False  
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']  # Erfan ip:port app ro bezar inja


# CORS settings 
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Erfan ip:port app ro bezar inja
    'http://127.0.0.1:3000',  
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mtt584388@gmail.com'  
EMAIL_HOST_PASSWORD = 'chcz rdmz qhtn natj'
DEFAULT_FROM_EMAIL = 'mtt584388@gmail.com'
EMAIL_USE_SSL = False  
EMAIL_TIMEOUT = 60 
# for macOS debugging
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CHECK_HOSTNAME = False

import platform
if platform.system() == 'Darwin':  # macOS
    EMAIL_SSL_VERIFY_MODE = ssl.CERT_NONE
else:
    EMAIL_SSL_VERIFY_MODE = ssl.CERT_REQUIRED




if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
