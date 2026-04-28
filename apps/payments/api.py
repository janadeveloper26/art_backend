from ninja import Router
from .schemas import SubscriptionPlansResponseSchema, CreateOrderSchema
from core.responses import success_response, StandardResponse
from core.permissions import AuthBearer
from core.exceptions import APIError
from core.idempotency import idempotent
from .models import SubscriptionPlan, Order
import uuid

router = Router()

@router.get("/plans", response={200: StandardResponse})
@idempotent(timeout=300)
def get_subscription_plans(request):
    # Fetch active subscription plans with features
    plans_qs = SubscriptionPlan.objects.filter(is_active=True).prefetch_related('features').order_by('order')
    
    plans = []
    for p in plans_qs:
        color_start = int(p.color_start, 16) if p.color_start.startswith('0x') else 0
        color_end = int(p.color_end, 16) if p.color_end.startswith('0x') else 0
        
        plans.append({
            "id": p.id,
            "label": p.label,
            "price": float(p.price),
            "original_price": float(p.original_price),
            "period": p.period,
            "icon": p.icon,
            "popular": p.popular,
            "savings": p.savings,
            "colors": [color_start, color_end],
            "features": [f.text for f in p.features.all()]
        })

    # Hardcoded or from a singleton Setting model
    data = {
        "header_title": "Unlock Premium",
        "header_subtitle": "Get unlimited access to all Aari & Tailoring courses and learn from expert instructors",
        "highlights": ["100+ Courses", "Live Classes", "Certificates", "Offline Access"],
        "testimonial": {
            "quote": "\"Subscribing to the yearly plan was the best decision. I completed 8 courses and now run my own embroidery business!\"",
            "author": "Sunitha Rao",
            "role": "Yearly subscriber",
            "initial": "S"
        },
        "plans": plans
    }
    return success_response(data=data)

@router.post("/create-order", auth=AuthBearer(), response={200: StandardResponse})
@idempotent(timeout=60)
def create_order(request, data: CreateOrderSchema):
    try:
        plan = SubscriptionPlan.objects.get(id=data.plan_id)
        amount = plan.price
    except SubscriptionPlan.DoesNotExist:
        raise APIError(400, "Invalid plan ID")
    
    # In production, call Razorpay/Stripe API here
    # order = razorpay_client.order.create({"amount": amount * 100, "currency": "INR", ...})
    
    # Create internal order record
    order = Order.objects.create(
        user=request.auth,
        plan=plan,
        amount=amount,
        status='PENDING'
    )
    
    order_data = {
        "order_id": f"order_{order.id.hex[:12]}",
        "amount": float(amount),
        "currency": "INR",
        "status": "created",
        "gateway_key": "rzp_test_..." # Public key for frontend
    }
    
    return success_response(data=order_data, message="Order created successfully")
