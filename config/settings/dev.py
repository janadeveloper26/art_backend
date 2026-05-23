from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*', '172.30.24.194', 'localhost', '127.0.0.1', '0.0.0.0']

# Disable HTTPS-only security for local dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
