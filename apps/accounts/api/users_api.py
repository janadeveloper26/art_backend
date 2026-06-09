from typing import List
from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models import DeviceSession
from apps.accounts.schemas import UserOutSchema

router = Router(tags=['Users'])
User = get_user_model()

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            if not user.is_staff:
                raise HttpError(403, "Admin privileges required")
            return user
        except Exception:
            raise HttpError(401, "Invalid token")

@router.get('/list', response=List[UserOutSchema], auth=JWTAuth())
def list_users(request):
    return User.objects.all().order_by('-date_joined')

@router.patch('/{user_id}/approve/', response=UserOutSchema, auth=JWTAuth())
def approve_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

    now = timezone.now()

    user.is_approved = True
    user.approved_at = now
    user.save()

    # Auto-approve all existing devices so the user isn't blocked
    # by a second approval gate on their next login.
    DeviceSession.objects.filter(user=user, is_approved=False).update(
        is_approved=True,
        approved_at=now,
        updated_at=now,
    )

    return user

