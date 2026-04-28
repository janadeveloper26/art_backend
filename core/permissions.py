import jwt
from django.conf import settings
from ninja.security import HttpBearer
from accounts.models import User

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id:
                return User.objects.get(id=user_id)
        except (jwt.PyJWTError, User.DoesNotExist):
            return None
        return None
