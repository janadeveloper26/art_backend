import os
import sys

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from ninja.testing import TestClient
from config.urls import api
from core.permissions import AuthBearer

# mock AuthBearer to always return a mock user
def mock_auth(request):
    return "test_user"

api.auth = mock_auth

client = TestClient(api)

response = client.post('/videos/signed-url', json={'file_name': 'test.mp4'})
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
