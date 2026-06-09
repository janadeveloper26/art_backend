from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*', '172.30.24.194', 'localhost', '127.0.0.1', '0.0.0.0','localhost:3000',]

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
