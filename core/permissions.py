import jwt
from django.conf import settings
from ninja.security import HttpBearer
# pyrefly: ignore [missing-import]
from accounts.models import User

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get('type') != 'access':
                return None
            
            user_id = payload.get("user_id")
            device_id = payload.get("device_id")
            
            if user_id:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    return None
                
                # Attach metadata for logging/middleware
                request.user_id = user_id
                request.device_id = device_id
                
                return user
        except (jwt.PyJWTError, User.DoesNotExist):
            return None
        return None
