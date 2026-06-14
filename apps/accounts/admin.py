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
