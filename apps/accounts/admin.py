from django.contrib import admin
from .models import User, AuthIdentity

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'name', 'skill_level', 'is_active', 'created_at')
    search_fields = ('email', 'phone', 'name')
    list_filter = ('skill_level', 'is_active')

@admin.register(AuthIdentity)
class AuthIdentityAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_uid', 'verified', 'created_at')
    list_filter = ('provider', 'verified')
