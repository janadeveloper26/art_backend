import os
import sys

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
import django
django.setup()

from ninja.testing import TestClient
from config.urls import api
from apps.courses.api import video_router

# mock AuthBearer to always return a mock user
def mock_auth(request):
    return "test_user"

# Find the router and override auth
for path, router in api._routers:
    if router == video_router:
        pass

client = TestClient(api)
api.auth = mock_auth

response = client.post('/videos/signed-url', json={'file_name': '35c08323-15ac-4eba-8efd-c37741ededad.mp4'})
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
