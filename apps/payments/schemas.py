from typing import List, Optional
from ninja import Schema

class TestimonialSchema(Schema):
    quote: str
    author: str
    role: str
    initial: str

class PlanSchema(Schema):
    id: str
    label: str
    price: int
    original_price: int
    period: str
    icon: str
    popular: bool = False
    savings: Optional[str] = None
    colors: List[int]
    features: List[str]

class SubscriptionPlansResponseSchema(Schema):
    header_title: str
    header_subtitle: str
    highlights: List[str]
    testimonial: TestimonialSchema
    plans: List[PlanSchema]

class CreateOrderSchema(Schema):
    plan_id: str

class OrderResponseSchema(Schema):
    order_id: str
    amount: int
    currency: str = "INR"
    status: str
    gateway_key: Optional[str] = None
