import logging
import uuid
from typing import Optional

from ninja import Router
from ninja.errors import HttpError

from core.permissions import AuthBearer
from core.responses import success_response, StandardResponse

from .models import SupplyCategory, Product, Order, OrderItem
from .schemas import CheckoutIn

logger = logging.getLogger('art_backend')

router = Router(tags=['Supply'])


# ---------------------------------------------------------------------------
# GET /supply/categories
# ---------------------------------------------------------------------------

@router.get('/categories', response={200: StandardResponse})
def get_categories(request):
    names = ['All'] + list(
        SupplyCategory.objects.order_by('order', 'name').values_list('name', flat=True)
    )
    return success_response(data=names)


# ---------------------------------------------------------------------------
# GET /supply/products
# ---------------------------------------------------------------------------

@router.get('/products', response={200: StandardResponse})
def get_products(request, category: Optional[str] = None, search: Optional[str] = None):
    """
    List active products.
    - ?category=Thread   – filter by category name ('All' = no filter)
    - ?search=cotton     – case-insensitive title/description search
    """
    qs = Product.objects.filter(is_active=True).select_related('category')

    if category and category.lower() != 'all':
        qs = qs.filter(category__name__iexact=category)

    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(description__icontains=search)

    data = []
    for p in qs:
        data.append({
            'id': str(p.id),
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'original_price': float(p.original_price),
            'image_url': p.image_url,
            'category': p.category.name if p.category else None,
            'rating': p.rating,
            'reviews_count': p.reviews_count,
            'in_stock': p.in_stock,
        })

    return success_response(data=data)


# ---------------------------------------------------------------------------
# POST /supply/checkout
# ---------------------------------------------------------------------------

@router.post('/checkout', response={200: StandardResponse}, auth=AuthBearer())
def checkout(request, payload: CheckoutIn):
    """
    Place a supply order for the authenticated user.
    Creates an Order and its OrderItems in a single transaction.
    """
    user = request.auth

    if not payload.items:
        raise HttpError(400, 'Cart is empty. Add items before checkout.')

    if not payload.shipping_address or not payload.shipping_address.strip():
        raise HttpError(400, 'Shipping address is required.')

    if payload.total_amount <= 0:
        raise HttpError(400, 'Invalid total amount.')

    # Validate UUIDs before querying DB
    product_ids = [item.product_id for item in payload.items]
    for pid in product_ids:
        try:
            uuid.UUID(pid)
        except (ValueError, AttributeError):
            raise HttpError(400, f'Invalid product ID: {pid}')

    products_map = {
        str(p.id): p
        for p in Product.objects.filter(id__in=product_ids, is_active=True, in_stock=True)
    }

    missing = [pid for pid in product_ids if pid not in products_map]
    if missing:
        raise HttpError(400, f"Products not available: {missing}")

    order = Order.objects.create(
        user=user,
        total_amount=payload.total_amount,
        shipping_address=payload.shipping_address,
    )

    order_items = [
        OrderItem(
            order=order,
            product=products_map[item.product_id],
            quantity=item.quantity,
            unit_price=products_map[item.product_id].price,
        )
        for item in payload.items
    ]
    OrderItem.objects.bulk_create(order_items)

    logger.info('Order %s placed by user %s for %s', order.id, user.id, payload.total_amount)

    return success_response(data={'order_id': str(order.id)}, message='Order placed successfully')
