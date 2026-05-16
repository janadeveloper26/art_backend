import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from core.exceptions import APIError
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # For development if path not set, initialize without credentials 
        # (will fail on actual verification but allow app to start)
        try:
            firebase_admin.initialize_app()
        except Exception:
            pass

class FirebaseService:
    @staticmethod
    def verify_token(token: str):
        if settings.DEBUG and token == "test-token-123":
            return {
                "uid": "mock-user-123",
                "email": "test@example.com",
                "phone_number": "+919876543210",
                "name": "Test User",
                "firebase": {"sign_in_provider": "google.com"}
            }
        
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise APIError(401, f"Invalid Firebase Token: {str(e)}")
