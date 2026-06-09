from django.conf import settings
from ninja import Router

from .schemas import CreateOrderSchema
from core.responses import success_response, StandardResponse
from core.permissions import AuthBearer
from core.exceptions import APIError
from core.idempotency import idempotent
from .models import SubscriptionPlan, Order

router = Router()


def _parse_color(hex_str: str, fallback: int = 0xFF6A1B9A) -> int:
    """Convert stored '0xFF6A1B9A' string to ARGB int."""
    try:
        return int(hex_str, 16)
    except (ValueError, TypeError):
        return fallback


@router.get('/plans', response={200: StandardResponse}, auth=AuthBearer())
@idempotent(timeout=300)
def get_subscription_plans(request):
    """Return all active subscription plans for the Subscription screen."""
    plans_qs = (
        SubscriptionPlan.objects.filter(is_active=True)
        .prefetch_related('features')
        .order_by('order')
    )

    plans = []
    for p in plans_qs:
        plans.append({
            'id': p.id,
            'label': p.label,
            'price': int(p.price),
            'original_price': int(p.original_price),
            'period': p.period,
            'icon': p.icon,
            'popular': p.popular,
            'savings': p.savings,
            'colors': [_parse_color(p.color_start), _parse_color(p.color_end)],
            'features': [f.text for f in p.features.all()],
        })

    data = {
        'header_title': 'Unlock Premium',
        'header_subtitle': 'Get unlimited access to all Aari & Tailoring courses',
        'highlights': ['100+ Courses', 'Live Classes', 'Certificates', 'Offline Access'],
        'testimonial': {
            'quote': '"Subscribing to the yearly plan was the best decision."',
            'author': 'Sunitha Rao',
            'role': 'Yearly subscriber',
            'initial': 'S',
        },
        'plans': plans,
    }
    return success_response(data=data, message='Subscription plans fetched successfully.')


@router.post('/create-order', auth=AuthBearer(), response={200: StandardResponse})
@idempotent(timeout=60)
def create_order(request, data: CreateOrderSchema):
    """Create a payment order for a subscription plan."""
    try:
        plan = SubscriptionPlan.objects.get(id=data.plan_id)
    except SubscriptionPlan.DoesNotExist:
        raise APIError(400, 'Invalid plan ID.')

    order = Order.objects.create(
        user=request.auth,
        plan=plan,
        amount=plan.price,
        status='PENDING',
    )

    order_data = {
        'order_id': f'order_{order.id.hex[:12]}',
        'amount': int(plan.price),
        'currency': 'INR',
        'status': 'created',
        'gateway_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
    return success_response(data=order_data, message='Order created successfully.')
