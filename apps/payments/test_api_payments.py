import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import DeviceSession
from apps.payments.models import SubscriptionPlan
from apps.courses.models import Course, Category
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class PaymentsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test-user',
            email='test@example.com',
            is_approved=True
        )
        
        DeviceSession.objects.create(
            user=self.user,
            device_id="device-123",
            device_name="Test Phone",
            is_approved=True
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        
        self.plan = SubscriptionPlan.objects.create(
            id="monthly",
            label="Pro Plan",
            price=999.00,
            original_price=1200.00,
            period="1 month",
            icon="star",
            is_active=True
        )

        self.category = Category.objects.create(name="Embroidery")
        self.course = Course.objects.create(
            title="Aari Masterclass",
            description="Learn Aari",
            category=self.category,
            price=500.00,
            is_published=True
        )

    def test_get_plans(self):
        response = self.client.get(
            '/api/v1/payments/plans',
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            secure=True
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))

    @patch('apps.payments.services.RazorpayService.create_course_order')
    @patch('apps.payments.services.getattr')
    def test_create_course_order(self, mock_getattr, mock_create_order):
        mock_getattr.return_value = 'mock_rzp_key'
        mock_create_order.return_value = {'id': 'order_mock123', 'amount': 50000, 'currency': 'INR', 'status': 'created'}
        
        payload = {"course_id": str(self.course.id)}
        
        response = self.client.post(
            '/api/v1/payments/courses/create-order',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            secure=True
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('order_id', data['data'])
        self.assertEqual(data['data']['amount'], self.course.price * 100)

    @patch('apps.payments.services.RazorpayService.create_subscription')
    @patch('apps.payments.services.getattr')
    def test_create_subscription(self, mock_getattr, mock_create_subscription):
        mock_getattr.return_value = 'mock_rzp_key'
        mock_create_subscription.return_value = {'id': 'sub_mock123', 'status': 'created'}
        
        payload = {"plan_id": str(self.plan.id)}
        
        response = self.client.post(
            '/api/v1/payments/subscriptions/create',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            secure=True
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('subscription_id', data['data'])
