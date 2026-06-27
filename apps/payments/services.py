import razorpay
from django.conf import settings

class RazorpayService:
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None

    def create_course_order(self, amount: int, currency: str = 'INR', receipt: str = None) -> dict:
        """
        Create a one-time Razorpay order for a course.
        Amount should be in paise.
        """
        if not self.client:
            return {
                "id": f"mock_order_{receipt}",
                "amount": amount,
                "currency": currency,
                "status": "created"
            }

        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": "1"
        }
        
        return self.client.order.create(data=data)

    def create_subscription(self, plan_id: str, total_count: int = 12) -> dict:
        """
        Create a Razorpay subscription.
        plan_id must match a Plan created in Razorpay dashboard.
        """
        if not self.client:
            return {
                "id": f"mock_sub_{plan_id}",
                "entity": "subscription",
                "plan_id": plan_id,
                "status": "created",
                "short_url": "https://rzp.io/i/mock"
            }

        data = {
            "plan_id": plan_id,
            "total_count": total_count,
            "customer_notify": 1
        }
        
        return self.client.subscription.create(data=data)

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verify the payment signature for course orders.
        """
        if not self.client:
            return True

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def verify_subscription_signature(self, razorpay_subscription_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verify the payment signature for subscriptions.
        """
        if not self.client:
            return True

        params_dict = {
            'razorpay_subscription_id': razorpay_subscription_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            self.client.utility.verify_subscription_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
