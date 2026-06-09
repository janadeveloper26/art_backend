import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_firebase_app = None


class FirebaseTokenError(RuntimeError):
    """Raised when a Firebase ID token is invalid for authentication."""


class FirebaseServiceUnavailableError(RuntimeError):
    """Raised when Firebase cannot verify a token due to service/connectivity issues."""


def initialize_firebase():
    global _firebase_app

    if _firebase_app:
        return _firebase_app

    try:
        # Try file-based credentials first
        service_account_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', '')
        if service_account_path:
            key_path = Path(settings.BASE_DIR) / service_account_path
            if key_path.exists():
                cred = credentials.Certificate(str(key_path))
                _firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized via service account file")
                return _firebase_app

        # Fall back to env-var credentials
        project_id = settings.FIREBASE_PROJECT_ID
        private_key = settings.FIREBASE_PRIVATE_KEY
        client_email = settings.FIREBASE_CLIENT_EMAIL

        if not all([project_id, private_key, client_email]):
            raise ValueError(
                "Firebase credentials missing. Set FIREBASE_SERVICE_ACCOUNT_PATH "
                "or FIREBASE_PROJECT_ID / FIREBASE_PRIVATE_KEY / FIREBASE_CLIENT_EMAIL in .env"
            )

        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized via environment variables")
        return _firebase_app

    except Exception as e:
        logger.exception("Firebase initialization failed")
        raise RuntimeError(f"Firebase initialization error: {e}")


def verify_firebase_token(id_token: str) -> dict:
    try:
        initialize_firebase()
        # Add a 60 second clock skew tolerance for device-server time differences
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=60)
        return decoded_token
    except (
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
        auth.UserDisabledError,
    ) as e:
        logger.warning("Firebase token rejected: %s", e)
        raise FirebaseTokenError("Invalid or expired Firebase token") from e
    except auth.CertificateFetchError as e:
        logger.exception("Firebase certificate fetch failed")
        raise FirebaseServiceUnavailableError(
            "Firebase token verification is temporarily unavailable"
        ) from e
    except Exception as e:
        logger.exception("Firebase token verification failed")
        raise FirebaseServiceUnavailableError(
            "Firebase token verification is temporarily unavailable"
        ) from e
