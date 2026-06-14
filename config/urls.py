from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.accounts.api.auth_api import router as auth_router
from apps.accounts.api.users_api import router as users_router
from apps.courses.api import router as courses_router
from apps.courses.api import video_router

api = NinjaAPI(
    title='ART API',
    version='1.0.0',
)

api.add_router('/auth/', auth_router)
api.add_router('/users/', users_router)
api.add_router('/courses/', courses_router)
api.add_router('/videos/', video_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
]


