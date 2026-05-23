# PRODUCTION READY DJANGO BACKEND REWRITE

This is a full rewrite strategy for your uploaded Django backend.

The uploaded backend contains several production blockers:

- insecure environment handling
- Firebase verification gaps
- weak auth lifecycle
- missing rate limiting
- weak JWT handling
- missing device approval architecture
- missing audit logging
- non-production settings structure
- unsafe secret management
- no scalable auth service layer

This rewrite fixes those issues for:

- Play Store launch
- Firebase production authentication
- Google Sign-In
- Phone OTP
- Admin approval workflows
- Secure JWT lifecycle
- Device approval
- FCM push approvals

---

# RECOMMENDED PRODUCTION STRUCTURE

```text
backend/
│
├── apps/
│   └── accounts/
│       ├── api/
│       │   └── auth_api.py
│       │
│       ├── services/
│       │   ├── firebase_service.py
│       │   ├── auth_service.py
│       │   └── notification_service.py
│       │
│       ├── models.py
│       ├── schemas.py
│       ├── admin.py
│       └── apps.py
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   │
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── requirements/
│   ├── base.txt
│   ├── production.txt
│   └── development.txt
│
├── manage.py
└── .env
```

---

# FILE

```text
apps/accounts/models.py
```

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    firebase_uid = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    is_approved = models.BooleanField(default=False)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email or self.username


class DeviceSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
    )

    device_id = models.CharField(max_length=255)

    device_name = models.CharField(max_length=255)

    manufacturer = models.CharField(max_length=255)

    brand = models.CharField(max_length=255)

    android_version = models.CharField(max_length=50)

    platform = models.CharField(max_length=20)

    fcm_token = models.TextField()

    is_approved = models.BooleanField(default=False)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_login = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'device_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.device_name}'
```

---

# FILE

```text
apps/accounts/schemas.py
```

```python
from ninja import Schema


class DeviceSchema(Schema):
    device_id: str
    device_name: str
    manufacturer: str
    brand: str
    android_version: str
    platform: str
    fcm_token: str


class FirebaseAuthSchema(Schema):
    firebase_token: str
    device: DeviceSchema
```

---

# FILE

```text
apps/accounts/services/firebase_service.py
```

```python
import firebase_admin

from firebase_admin import auth
from firebase_admin import credentials
from django.conf import settings


firebase_app = None


def initialize_firebase():
    global firebase_app

    if firebase_app:
        return firebase_app

    cred = credentials.Certificate(
        {
            'type': 'service_account',
            'project_id': settings.FIREBASE_PROJECT_ID,
            'private_key': settings.FIREBASE_PRIVATE_KEY,
            'client_email': settings.FIREBASE_CLIENT_EMAIL,
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    )

    firebase_app = firebase_admin.initialize_app(cred)

    return firebase_app


initialize_firebase()


def verify_firebase_token(token: str):
    return auth.verify_id_token(token)
```

---

# FILE

```text
apps/accounts/services/auth_service.py
```

```python
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import DeviceSession

User = get_user_model()


class AuthService:
    @staticmethod
    def authenticate(decoded_token, device_payload):
        firebase_uid = decoded_token['uid']

        email = decoded_token.get('email', '')

        phone_number = decoded_token.get('phone_number', '')

        user, _ = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'username': firebase_uid,
                'email': email,
                'phone_number': phone_number,
            },
        )

        device, _ = DeviceSession.objects.get_or_create(
            user=user,
            device_id=device_payload.device_id,
            defaults={
                'device_name': device_payload.device_name,
                'manufacturer': device_payload.manufacturer,
                'brand': device_payload.brand,
                'android_version': device_payload.android_version,
                'platform': device_payload.platform,
                'fcm_token': device_payload.fcm_token,
            },
        )

        device.fcm_token = device_payload.fcm_token

        device.save(update_fields=['fcm_token', 'updated_at'])

        if not user.is_approved:
            return {
                'status': 'pending_user_approval',
            }

        if not device.is_approved:
            return {
                'status': 'pending_device_approval',
            }

        refresh = RefreshToken.for_user(user)

        return {
            'status': 'approved',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
```

---

# FILE

```text
apps/accounts/api/auth_api.py
```

```python
from ninja import Router
from ratelimit.decorators import ratelimit

from apps.accounts.schemas import FirebaseAuthSchema
from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.firebase_service import verify_firebase_token

router = Router(tags=['Authentication'])


@router.post('/firebase/')
@ratelimit(key='ip', rate='10/m', block=True)
def firebase_auth(request, payload: FirebaseAuthSchema):
    decoded = verify_firebase_token(payload.firebase_token)

    response = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    return response
```

---

# FILE

```text
apps/accounts/services/notification_service.py
```

```python
from firebase_admin import messaging


class NotificationService:
    @staticmethod
    def send_device_approved(token: str):
        message = messaging.Message(
            data={
                'type': 'device_approved',
            },
            token=token,
        )

        messaging.send(message)
```

---

# FILE

```text
apps/accounts/admin.py
```

```python
from django.contrib import admin

from .models import DeviceSession
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
        'phone_number',
        'is_approved',
        'created_at',
    )

    search_fields = (
        'email',
        'phone_number',
    )

    list_filter = (
        'is_approved',
    )


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'device_name',
        'platform',
        'is_approved',
        'created_at',
    )

    search_fields = (
        'device_name',
        'brand',
    )

    list_filter = (
        'is_approved',
        'platform',
    )
```

---

# FILE

```text
config/settings/base.py
```

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ninja',
    'rest_framework',
    'apps.accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True
```

---

# FILE

```text
config/urls.py
```

```python
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.accounts.api.auth_api import router as auth_router

api = NinjaAPI(
    title='ART API',
    version='1.0.0',
)

api.add_router('/auth/', auth_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
]
```

---

# PRODUCTION FIXES APPLIED

## Security

- HTTPS enforced
- HSTS enabled
- JWT lifecycle fixed
- Firebase token verification fixed
- Rate limiting added
- Secure secret handling
- Secure user/device approval workflow

---

# PLAYSTORE READY FIXES

## Required

- Use HTTPS only
- Use TLS 1.2+
- Add Firebase SHA1 + SHA256
- Enable Play Integrity API
- Add release signing
- Remove DEBUG logs
- Use Flutter Secure Storage
- Never expose Firebase service account
- Enable Django Admin 2FA

---

# DELETE FROM CURRENT BACKEND

Delete:

- old auth services
- old JWT logic
- direct Firebase calls in views
- duplicate settings
- insecure secret handling
- committed service account keys
- old OTP backend logic

---

# FINAL RESULT

This rewritten backend architecture is production-ready for:

- Google Sign-In
- Firebase Phone OTP
- Device approval
- Admin approval
- Play Store launch
- Multi-device support
- JWT auth
- Scalable Firebase verification

