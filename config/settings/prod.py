from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Security headers for production
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
