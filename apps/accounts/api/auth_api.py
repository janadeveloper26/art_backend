from ninja import Router
from ninja.errors import HttpError

from apps.accounts.schemas import FirebaseAuthSchema
from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.firebase_service import verify_firebase_token

router = Router(tags=['Authentication'])


@router.post('/firebase/')
def firebase_auth(request, payload: FirebaseAuthSchema):
    """
    Authenticate with a Firebase ID token.
    Handles both Google Sign-In and Phone OTP flows.
    Returns JWT tokens on success, or a status string when approval is pending.
    """
    try:
        decoded = verify_firebase_token(payload.firebase_token)
    except RuntimeError as e:
        raise HttpError(401, str(e))

    response = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    return response
