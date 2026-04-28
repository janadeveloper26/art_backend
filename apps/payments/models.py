import uuid
from django.db import models
from accounts.models import User
from courses.models import Course

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'

class SubscriptionPlan(models.Model):
    id = models.CharField(primary_key=True, max_length=50) # e.g., 'monthly', 'yearly'
    label = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=50)
    icon = models.CharField(max_length=50)
    popular = models.BooleanField(default=False)
    savings = models.CharField(max_length=100, null=True, blank=True)
    color_start = models.CharField(max_length=20, default="0xFF6A1B9A")
    color_end = models.CharField(max_length=20, default="0xFFAB47BC")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscription_plans'
        ordering = ['order']

class PlanFeature(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'plan_features'
        ordering = ['order']

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'

