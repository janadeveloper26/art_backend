from .base import *

if SECRET_KEY == 'django-insecure-change-me':
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("SECRET_KEY must be set in production.")

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=['*'])

# Security headers for production
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'prod.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'art_backend': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Fix for django-ratelimit behind a reverse proxy (like Nginx)
RATELIMIT_IP_META_KEY = 'HTTP_X_FORWARDED_FOR'
