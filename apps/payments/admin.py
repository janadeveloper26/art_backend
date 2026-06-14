from django.contrib import admin
from .models import SubscriptionPlan, PlanFeature, Order


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'price', 'popular', 'is_active', 'order')
    list_filter = ('is_active', 'popular')
    inlines = [PlanFeatureInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status',)
