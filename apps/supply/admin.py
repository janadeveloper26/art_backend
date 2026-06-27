from django.contrib import admin
from .models import SupplyCategory, Product, Order, OrderItem


@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order', 'name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'in_stock', 'is_active', 'rating')
    list_filter = ('category', 'in_stock', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__phone_number')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)
