from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me')

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'corsheaders',
    'ninja',
    'rest_framework',
    'rest_framework_simplejwt',
    'storages',
    # Local
    'apps.accounts',
    'apps.courses',
    'apps.notifications',
    'apps.payments',
    # 'apps.analytics',
    'apps.audit',
    # 'apps.supply',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ApiLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME', default='glourious_art'),
        'USER': env('DB_USER', default='root'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
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

# Simple JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Firebase
FIREBASE_PROJECT_ID = env('FIREBASE_PROJECT_ID', default='')
FIREBASE_PRIVATE_KEY = env('FIREBASE_PRIVATE_KEY', default='').replace('\\n', '\n')
FIREBASE_CLIENT_EMAIL = env('FIREBASE_CLIENT_EMAIL', default='')
FIREBASE_SERVICE_ACCOUNT_PATH = env('FIREBASE_SERVICE_ACCOUNT_PATH', default='')

# Cache (django-ratelimit uses cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# AWS S3 — presigned URLs for video upload
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='mock_access_key')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='mock_secret_key')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='mock-bucket')
AWS_S3_REGION = env('AWS_S3_REGION', default=env('AWS_S3_REGION_NAME', default='us-east-1'))
AWS_S3_REGION_NAME = AWS_S3_REGION

# CloudFront — video streaming distribution (optional)
CLOUDFRONT_DOMAIN = env('CLOUDFRONT_DOMAIN', default=env('AWS_S3_CUSTOM_DOMAIN', default=None))
CLOUDFRONT_KEY_ID = env('CLOUDFRONT_KEY_ID', default=None)
_raw_cf_private = env('CLOUDFRONT_PRIVATE_KEY', default=None)
if _raw_cf_private and '-----' not in _raw_cf_private:
    _p = Path(_raw_cf_private)
    if not _p.is_absolute():
        _raw_cf_private = str(BASE_DIR / _p)
CLOUDFRONT_PRIVATE_KEY = _raw_cf_private
AWS_S3_CUSTOM_DOMAIN = CLOUDFRONT_DOMAIN

# Razorpay
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='')
