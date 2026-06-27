from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    firebase_uid = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        default=None,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    is_approved = models.BooleanField(default=False)
    
    is_premium = models.BooleanField(default=False)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    avatar = models.URLField(
        max_length=500,
        blank=True,
        default='',
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
