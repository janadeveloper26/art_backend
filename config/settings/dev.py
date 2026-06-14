from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*','//192.168.29.72', '172.30.24.194', 'localhost', '127.0.0.1', '0.0.0.0','localhost:3000','unread-agreeably-perfected.ngrok-free.dev']

# Disable HTTPS-only security for local dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Enable django-extensions in development for runserver_plus
try:
	INSTALLED_APPS += ["django_extensions"]
except NameError:
	INSTALLED_APPS = ["django_extensions"]

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
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'dev.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'art_backend': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
