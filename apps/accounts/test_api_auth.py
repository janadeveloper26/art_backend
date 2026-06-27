import json
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import DeviceSession

User = get_user_model()

class AuthAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test-user',
            firebase_uid='firebase-test-uid-123',
            phone_number='+1234567890',
            is_approved=True,
        )

    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_firebase_login_success(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'firebase-test-uid-123',
            'email': 'test@example.com'
        }
        
        payload = {
            "firebase_token": "valid-token",
            "name": "Test User",
            "email": "test@example.com",
            "device": {
                "device_id": "device-123",
                "device_name": "Test Phone"
            }
        }
        
        response = self.client.post(
            '/api/v1/auth/firebase/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access_token', data['data'])
        self.assertIn('refresh_token', data['data'])

    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_firebase_login_pending_approval(self, mock_verify):
        # Create unapproved user
        User.objects.create_user(
            username='pending-user',
            firebase_uid='firebase-pending',
            is_approved=False,
        )
        mock_verify.return_value = {
            'uid': 'firebase-pending'
        }
        
        payload = {
            "firebase_token": "valid-token",
            "device": {
                "device_id": "device-456",
                "device_name": "Pending Phone"
            }
        }
        
        response = self.client.post(
            '/api/v1/auth/firebase/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 422)
        
    def test_send_otp_success(self):
        payload = {
            "phone_number": "+1234567890"
        }
        
        response = self.client.post(
            '/api/v1/auth/send-otp',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['data']['is_existing_user'])
        
    @patch('apps.accounts.api.auth_api.verify_firebase_token')
    def test_otp_verify_success(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'firebase-test-uid-123',
            'phone_number': '+1234567890'
        }
        
        payload = {
            "id_token": "valid-token",
            "device": {
                "device_id": "device-123",
                "device_name": "Test Phone"
            }
        }
        
        response = self.client.post(
            '/api/v1/auth/otp/verify',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access_token', data['data'])

    def test_device_approval_status(self):
        DeviceSession.objects.create(
            user=self.user,
            device_id="device-123",
            device_name="Test Phone",
            is_approved=True
        )
        
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        response = self.client.get(
            '/api/v1/auth/device/approval-status',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['data']['is_approved'])
