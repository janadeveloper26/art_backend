from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.accounts.api.auth_api import router as auth_router

api = NinjaAPI(
    title='ART API',
    version='1.0.0',
)

api.add_router('/auth/', auth_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
]
