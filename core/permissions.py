from ninja.security import HttpBearer
from ninja.errors import HttpError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class AuthBearer(HttpBearer):
    """
    JWT Bearer auth using djangorestframework-simplejwt.
    Validates the access token issued by /auth/otp/verify and /auth/firebase/login.
    Raises 401 for missing/invalid/expired tokens.
    """

    def authenticate(self, request, token: str):
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
        except (InvalidToken, TokenError):
            raise HttpError(401, "Invalid or expired token.")

        if not user.is_active:
            raise HttpError(401, "User account is inactive.")

        if not user.is_approved:
            raise HttpError(403, "Account is not yet approved.")

        return user
