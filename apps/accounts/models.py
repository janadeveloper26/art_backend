import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager

class SkillLevel(models.TextChoices):
    BEGINNER = 'BEGINNER', 'Beginner'
    INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
    ADVANCED = 'ADVANCED', 'Advanced'

class UserStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACTIVE = 'ACTIVE', 'Active'
    BLOCKED = 'BLOCKED', 'Blocked'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    DELETED = 'DELETED', 'Deleted'

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    skill_level = models.CharField(
        max_length=20, 
        choices=SkillLevel.choices, 
        default=SkillLevel.BEGINNER
    )
    status = models.CharField(
        max_length=20, 
        choices=UserStatus.choices, 
        default=UserStatus.PENDING
    )
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return self.status == UserStatus.ACTIVE

    @is_active.setter
    def is_active(self, value):
        if value:
            self.status = UserStatus.ACTIVE
        else:
            if self.status == UserStatus.ACTIVE:
                self.status = UserStatus.SUSPENDED

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email if self.email else str(self.id)

class AuthProvider(models.TextChoices):
    GOOGLE = 'GOOGLE', 'Google'
    OTP = 'OTP', 'OTP'

class AuthIdentity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='identities')
    provider = models.CharField(max_length=20, choices=AuthProvider.choices)
    provider_uid = models.CharField(max_length=255) # For google: sub, for OTP: phone
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_identities'
        unique_together = ('provider', 'provider_uid')
