import uuid
from django.db import models
from django.conf import settings

class DeviceStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    BLOCKED = 'BLOCKED', 'Blocked'

class UserDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='devices'
    )
    install_id = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20)
    device_model = models.CharField(max_length=255, null=True, blank=True)
    os_version = models.CharField(max_length=20, null=True, blank=True)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    app_version = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=DeviceStatus.choices, 
        default=DeviceStatus.PENDING
    )
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_devices'
        verbose_name = 'User Device'
        verbose_name_plural = 'User Devices'

    def __str__(self):
        return f"{self.user.name} - {self.device_model} ({self.install_id})"
