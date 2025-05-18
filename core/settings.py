import os
from pathlib import Path
from datetime import timedelta
from django.conf import settings


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4@#)6&!$@^@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!3g1v2z5j0x7q8h3b9z1&*4$@!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
    # 'corsheaders',
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
            BASE_DIR / 'frontend',  # frontend files
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

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    # BASE_DIR / 'frontend/static',  # Next.js static files
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



#  Django Rest Framework settings
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
    'USE_SESSION_AUTH': False, # اگر فقط از توکن استفاده می‌کنید
    # این بخش مهم است:
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # با تنظیم این، drf-yasg سعی می‌کند به طور خودکار security را بر اساس permission_classes اعمال کند
    'AUTO_SCHEMA_TYPE_INSPECTORS': [
        'drf_yasg.inspectors.SwaggerAutoSchema',
        'drf_yasg.inspectors.CoreAPICompatInspector',
    ],
    'DEFAULT_AUTO_SCHEMA_CLASS': 'drf_yasg.inspectors.SwaggerAutoSchema',
    "DEFAULT_TAGS": []
}



# CSRF settings for Next.js integration
CSRF_COOKIE_SAMESITE = 'Lax'  # or 'None' if using cross-site requests with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to the CSRF token
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']  # Add your Next.js development server

# # CORS settings if your Next.js app is served separately in development
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:3000',  # Next.js development server
#     # Add your production domain here
# ]


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mtt584388@gmail.com'  
EMAIL_HOST_PASSWORD = 'chcz rdmz qhtn natj'  
DEFAULT_FROM_EMAIL = 'mtt584388@gmail.com'


# For production, consider adding:
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
