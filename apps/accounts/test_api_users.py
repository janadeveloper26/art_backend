from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UsersAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin-user',
            email='admin@example.com',
            password='password123'
        )
        self.normal_user = User.objects.create_user(
            username='normal-user',
            email='user@example.com',
            is_approved=False
        )
        
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)
        
        refresh_normal = RefreshToken.for_user(self.normal_user)
        self.normal_token = str(refresh_normal.access_token)

    def test_list_users_as_admin(self):
        response = self.client.get(
            '/api/v1/users/list',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 2)
        
    def test_list_users_as_normal_user_fails(self):
        response = self.client.get(
            '/api/v1/users/list',
            HTTP_AUTHORIZATION=f'Bearer {self.normal_token}'
        )
        self.assertEqual(response.status_code, 401)
        
    def test_approve_user_success(self):
        response = self.client.patch(
            f'/api/v1/users/{self.normal_user.id}/approve/',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_approved)
        self.assertIsNotNone(self.normal_user.approved_at)

    def test_approve_user_unauthorized(self):
        response = self.client.patch(
            f'/api/v1/users/{self.normal_user.id}/approve/',
            HTTP_AUTHORIZATION=f'Bearer {self.normal_token}'
        )
        self.assertEqual(response.status_code, 401)
