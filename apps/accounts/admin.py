from django.contrib import admin
from .models import User, AuthIdentity

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'name', 'skill_level', 'status', 'is_staff', 'created_at')
    search_fields = ('email', 'phone', 'name')
    list_filter = ('skill_level', 'status', 'is_staff')
    actions = ['activate_users', 'block_users']

    def activate_users(self, request, queryset):
        queryset.update(status='ACTIVE')
    activate_users.short_description = "Activate selected users"

    def block_users(self, request, queryset):
        queryset.update(status='BLOCKED')
    block_users.short_description = "Block selected users"

@admin.register(AuthIdentity)
class AuthIdentityAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_uid', 'verified', 'created_at')
    list_filter = ('provider', 'verified')
