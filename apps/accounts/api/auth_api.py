import logging

from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit

from ninja import Router
from ninja.errors import HttpError

from apps.accounts.schemas import FirebaseAuthSchema, AdminLoginSchema, OtpRequestSchema, OtpVerifySchema, TokenRefreshIn
from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.firebase_service import (
    FirebaseServiceUnavailableError,
    FirebaseTokenError,
    verify_firebase_token,
)
from apps.accounts.models import DeviceSession
from core.permissions import AuthBearer
from core.responses import success_response, error_response

logger = logging.getLogger('art_backend')

User = get_user_model()

router = Router(tags=['Authentication'])


# ---------------------------------------------------------------------------
# GET /auth/device/approval-status
# ---------------------------------------------------------------------------

@router.get('/device/approval-status', auth=AuthBearer())
def device_approval_status(request):
    user = request.auth
    device = DeviceSession.objects.filter(user=user).order_by('-created_at').first()

    is_approved = user.is_approved and (device.is_approved if device else True)
    return success_response(data={'is_approved': is_approved})


# ---------------------------------------------------------------------------
# POST /auth/admin-login
# ---------------------------------------------------------------------------

@router.post('/admin-login')
@ratelimit(key='ip', rate='10/m', block=True)
def admin_login(request, payload: AdminLoginSchema):
    username = payload.username
    if '@' in username:
        user_obj = User.objects.filter(email=username).first()
        if user_obj:
            username = user_obj.username

    user = authenticate(username=username, password=payload.password)
    if not user or not (user.is_staff or user.is_superuser):
        raise HttpError(401, "Invalid credentials or not an admin")

    refresh = RefreshToken.for_user(user)
    return success_response(data={
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


# ---------------------------------------------------------------------------
# POST /auth/token/refresh
# ---------------------------------------------------------------------------

@router.post('/token/refresh')
def token_refresh(request, payload: TokenRefreshIn):
    """Accepts a refresh token and returns a new access token."""
    if not payload.refresh_token or not payload.refresh_token.strip():
        raise HttpError(400, 'refresh_token is required.')

    try:
        refresh = RefreshToken(payload.refresh_token)
        new_access = str(refresh.access_token)
    except TokenError as e:
        logger.warning('Token refresh failed: %s', e)
        raise HttpError(401, 'Invalid or expired refresh token.')

    return success_response(data={'access_token': new_access}, message='Token refreshed successfully.')


# ---------------------------------------------------------------------------
# POST /auth/token/verify
# ---------------------------------------------------------------------------

@router.post('/token/verify')
def token_verify(request, payload: TokenRefreshIn):
    """Check whether an access or refresh token is still valid."""
    token = payload.refresh_token
    if not token or not token.strip():
        raise HttpError(400, 'token is required.')

    try:
        AccessToken(token)
        is_valid = True
    except TokenError:
        is_valid = False

    return success_response(data={'valid': is_valid}, message='Token verification complete.')


# ---------------------------------------------------------------------------
# POST /auth/firebase/login
# ---------------------------------------------------------------------------

@router.post('/firebase/login')
@ratelimit(key='ip', rate='10/m', block=True)
def firebase_auth(request, payload: FirebaseAuthSchema):
    """
    Authenticate with a Firebase ID token (Google Sign-In).
    Returns JWT tokens on success, or 422 when approval is pending.
    """
    try:
        decoded = verify_firebase_token(payload.firebase_token)
    except FirebaseTokenError as e:
        raise HttpError(401, str(e))
    except FirebaseServiceUnavailableError as e:
        raise HttpError(503, str(e))

    result = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    if result.get('pending'):
        raise HttpError(422, result['message'])

    if result.get('success'):
        firebase_uid = decoded.get('uid') or decoded.get('user_id') or decoded.get('sub')
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        if user:
            update_fields = []
            if payload.name and not user.first_name and not user.last_name:
                user.first_name = payload.name
                update_fields.append('first_name')
            if payload.email and not user.email:
                user.email = payload.email
                update_fields.append('email')
            if payload.avatar and not user.avatar:
                user.avatar = payload.avatar
                update_fields.append('avatar')
            if update_fields:
                user.save(update_fields=update_fields)
            if 'user' in result.get('data', {}):
                result['data']['user']['name'] = user.get_full_name() or user.username
                result['data']['user']['email'] = user.email
                result['data']['user']['avatar'] = user.avatar or None

    return result


# ---------------------------------------------------------------------------
# POST /auth/send-otp
# ---------------------------------------------------------------------------

@router.post('/send-otp')
@ratelimit(key='ip', rate='5/m', block=True)
def otp_request(request, payload: OtpRequestSchema):
    phone = payload.phone_number or payload.phone
    is_existing = User.objects.filter(phone_number=phone).exists() if phone else False
    return success_response(
        data={"is_existing_user": is_existing, "can_proceed": True},
        message="OTP sent successfully",
    )


# ---------------------------------------------------------------------------
# POST /auth/otp/verify
# ---------------------------------------------------------------------------

@router.post('/otp/verify')
@ratelimit(key='ip', rate='5/m', block=True)
def otp_verify(request, payload: OtpVerifySchema):
    """
    Verify Firebase ID token from phone OTP and authenticate.
    Returns 422 with 'pending admin approval' message when blocked.
    """
    try:
        decoded = verify_firebase_token(payload.id_token)
    except FirebaseTokenError as e:
        raise HttpError(401, str(e))
    except FirebaseServiceUnavailableError as e:
        raise HttpError(503, str(e))

    result = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    if result.get('pending'):
        raise HttpError(422, result['message'])

    if result.get('success'):
        firebase_uid = decoded.get('uid') or decoded.get('user_id') or decoded.get('sub')
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        if user:
            update_fields = []
            if payload.name and not user.first_name and not user.last_name:
                user.first_name = payload.name
                update_fields.append('first_name')
            if payload.email and not user.email:
                user.email = payload.email
                update_fields.append('email')
            if payload.avatar and not user.avatar:
                user.avatar = payload.avatar
                update_fields.append('avatar')
            if update_fields:
                user.save(update_fields=update_fields)
            if 'user' in result.get('data', {}):
                result['data']['user']['name'] = user.get_full_name() or user.username
                result['data']['user']['email'] = user.email
                result['data']['user']['avatar'] = user.avatar or None

    logger.info(f"OTP verify success for uid={decoded.get('uid')}")
    return result
