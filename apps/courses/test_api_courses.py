from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.courses.models import Course, Category
from apps.accounts.models import DeviceSession
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class CoursesAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test-user',
            email='test@example.com',
            is_approved=True
        )
        
        # We need an approved device session to pass AuthBearer
        DeviceSession.objects.create(
            user=self.user,
            device_id="device-123",
            device_name="Test Phone",
            is_approved=True
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        
        # Create test data
        self.category = Category.objects.create(name='Art Basics')
        self.course = Course.objects.create(
            title='Intro to Drawing',
            description='Learn to draw',
            category=self.category,
            price=99.99,
            is_published=True
        )

    def test_get_courses_home(self):
        response = self.client.get(
            '/api/v1/courses/home',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))

    def test_get_courses_explore(self):
        response = self.client.get(
            '/api/v1/courses/explore',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))

    def test_get_course_detail(self):
        response = self.client.get(
            f'/api/v1/courses/{self.course.id}',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))

    def test_get_my_courses(self):
        response = self.client.get(
            '/api/v1/courses/my-courses',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))
