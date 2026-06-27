import logging
from django.conf import settings
from django.db import DatabaseError, transaction
from django.contrib.contenttypes.models import ContentType
from ninja import Router

from .schemas import (
    CreateCourseOrderSchema, 
    CreateSubscriptionSchema, 
    VerifyCoursePaymentSchema,
    VerifySubscriptionPaymentSchema
)
from core.responses import success_response, StandardResponse
from core.permissions import AuthBearer
from core.exceptions import APIError
from core.idempotency import idempotent
from .models import SubscriptionPlan, CourseOrder, SubscriptionOrder, PaymentTransaction, PaymentStatus
from apps.courses.models import Course, Enrollment

logger = logging.getLogger('art_backend')

router = Router(tags=['Payments'])

def _parse_color(hex_str: str, fallback: int = 0xFF6A1B9A) -> int:
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

@router.post('/courses/create-order', auth=AuthBearer(), response={200: StandardResponse})
@idempotent(timeout=60)
def create_course_order(request, data: CreateCourseOrderSchema):
    """Create a payment order for a single course purchase."""
    from .services import RazorpayService
    try:
        course = Course.objects.get(id=data.course_id)
    except Course.DoesNotExist:
        raise APIError(404, 'Course not found.')

    amount_in_paise = int(course.price * 100)
    razorpay_service = RazorpayService()

    try:
        order = CourseOrder.objects.create(
            user=request.auth,
            course=course,
            amount=course.price,
            status=PaymentStatus.PENDING,
        )
        
        rzp_order = razorpay_service.create_course_order(
            amount=amount_in_paise,
            currency='INR',
            receipt=str(order.id)
        )
        
        order.gateway_order_id = rzp_order['id']
        order.save()
    except DatabaseError as e:
        logger.error('Course Order creation failed: %s', e)
        raise APIError(500, 'Failed to create order. Please try again.')
    except Exception as e:
        logger.error('Razorpay API error: %s', e)
        raise APIError(500, 'Failed to connect to payment gateway.')

    order_data = {
        'order_id': rzp_order['id'],
        'amount': amount_in_paise,
        'currency': rzp_order.get('currency', 'INR'),
        'status': rzp_order.get('status', 'created'),
        'gateway_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
    return success_response(data=order_data, message='Course order created successfully.')

@router.post('/courses/verify', auth=AuthBearer(), response={200: StandardResponse})
def verify_course_payment(request, data: VerifyCoursePaymentSchema):
    """Verify the Razorpay payment signature for a course and enroll the user."""
    from .services import RazorpayService
    razorpay_service = RazorpayService()
    
    is_valid = razorpay_service.verify_payment_signature(
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature
    )
    
    if not is_valid:
        raise APIError(400, "Invalid payment signature")
        
    try:
        with transaction.atomic():
            order = CourseOrder.objects.select_for_update().get(gateway_order_id=data.razorpay_order_id)
            
            if order.status == PaymentStatus.SUCCESS:
                return success_response(message="Payment already verified.")
                
            order.status = PaymentStatus.SUCCESS
            order.save()
            
            # Record Transaction
            ct = ContentType.objects.get_for_model(CourseOrder)
            PaymentTransaction.objects.create(
                user=request.auth,
                gateway_payment_id=data.razorpay_payment_id,
                gateway_signature=data.razorpay_signature,
                amount=order.amount,
                content_type=ct,
                object_id=order.id,
                status=PaymentStatus.SUCCESS
            )
            
            # Enroll user
            Enrollment.objects.get_or_create(user=request.auth, course=order.course)
            
        return success_response(message="Course payment verified successfully.")
    except CourseOrder.DoesNotExist:
        raise APIError(404, "Order not found")

@router.post('/subscriptions/create', auth=AuthBearer(), response={200: StandardResponse})
@idempotent(timeout=60)
def create_subscription(request, data: CreateSubscriptionSchema):
    """Create a subscription using Razorpay Subscriptions API."""
    from .services import RazorpayService
    try:
        plan = SubscriptionPlan.objects.get(id=data.plan_id)
    except SubscriptionPlan.DoesNotExist:
        raise APIError(404, 'Subscription plan not found.')

    if not plan.is_active:
        raise APIError(400, 'This plan is no longer available.')

    razorpay_service = RazorpayService()

    try:
        sub_order = SubscriptionOrder.objects.create(
            user=request.auth,
            plan=plan,
            amount=plan.price,
            status=PaymentStatus.PENDING,
        )
        
        # In a real scenario, plan_id maps to a Razorpay Plan ID
        rzp_sub = razorpay_service.create_subscription(
            plan_id=plan.id,
            total_count=12
        )
        
        sub_order.gateway_subscription_id = rzp_sub['id']
        sub_order.save()
    except DatabaseError as e:
        logger.error('Subscription creation failed: %s', e)
        raise APIError(500, 'Failed to create subscription. Please try again.')
    except Exception as e:
        logger.error('Razorpay API error: %s', e)
        raise APIError(500, 'Failed to connect to payment gateway.')

    sub_data = {
        'subscription_id': rzp_sub['id'],
        'status': rzp_sub.get('status', 'created'),
        'gateway_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
    return success_response(data=sub_data, message='Subscription created successfully.')

@router.post('/subscriptions/verify', auth=AuthBearer(), response={200: StandardResponse})
def verify_subscription_payment(request, data: VerifySubscriptionPaymentSchema):
    """Verify the Razorpay subscription signature and grant premium access."""
    from .services import RazorpayService
    razorpay_service = RazorpayService()
    
    is_valid = razorpay_service.verify_subscription_signature(
        data.razorpay_subscription_id,
        data.razorpay_payment_id,
        data.razorpay_signature
    )
    
    if not is_valid:
        raise APIError(400, "Invalid payment signature")
        
    try:
        with transaction.atomic():
            sub_order = SubscriptionOrder.objects.select_for_update().get(gateway_subscription_id=data.razorpay_subscription_id)
            
            if sub_order.status == PaymentStatus.SUCCESS:
                return success_response(message="Subscription already verified.")
                
            sub_order.status = PaymentStatus.SUCCESS
            sub_order.save()
            
            # Record Transaction
            ct = ContentType.objects.get_for_model(SubscriptionOrder)
            PaymentTransaction.objects.create(
                user=request.auth,
                gateway_payment_id=data.razorpay_payment_id,
                gateway_signature=data.razorpay_signature,
                amount=sub_order.amount,
                content_type=ct,
                object_id=sub_order.id,
                status=PaymentStatus.SUCCESS
            )
            
            # Grant premium access
            request.auth.is_premium = True
            request.auth.save()
            
        return success_response(message="Subscription verified successfully.")
    except SubscriptionOrder.DoesNotExist:
        raise APIError(404, "Subscription not found")
