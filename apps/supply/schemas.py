from typing import List, Optional
from ninja import Schema


class ProductOut(Schema):
    id: str
    name: str
    description: str
    price: float
    original_price: float
    image_url: str
    category: Optional[str] = None
    rating: float
    reviews_count: int
    in_stock: bool


class CheckoutItemIn(Schema):
    product_id: str
    quantity: int


class CheckoutIn(Schema):
    items: List[CheckoutItemIn]
    total_amount: float
    shipping_address: str
