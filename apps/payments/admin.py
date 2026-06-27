from django.contrib import admin
from .models import SubscriptionPlan, PlanFeature, CourseOrder, SubscriptionOrder, PaymentTransaction

class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'price', 'period', 'is_active', 'order')
    list_filter = ('is_active', 'popular')
    search_fields = ('id', 'label')
    inlines = [PlanFeatureInline]

@admin.register(CourseOrder)
class CourseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'gateway_order_id')

@admin.register(SubscriptionOrder)
class SubscriptionOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'gateway_subscription_id')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'gateway_payment_id', 'amount', 'status', 'created_at')
    search_fields = ('user__email', 'gateway_payment_id')
