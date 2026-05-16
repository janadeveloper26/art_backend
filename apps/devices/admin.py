from django.contrib import admin
from .models import UserDevice, DeviceStatus

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_model', 'platform', 'status', 'last_login_at', 'created_at')
    list_filter = ('status', 'platform')
    search_fields = ('user__name', 'user__email', 'install_id')
    actions = ['approve_devices', 'block_devices']

    def approve_devices(self, request, queryset):
        queryset.update(status=DeviceStatus.APPROVED)
    approve_devices.short_description = "Approve selected devices"

    def block_devices(self, request, queryset):
        queryset.update(status=DeviceStatus.BLOCKED)
    block_devices.short_description = "Block selected devices"
