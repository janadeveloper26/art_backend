from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from ninja import Router
from ninja.errors import HttpError

from apps.accounts.schemas import FirebaseAuthSchema, AdminLoginSchema, OtpRequestSchema, OtpVerifySchema
from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.firebase_service import (
    FirebaseServiceUnavailableError,
    FirebaseTokenError,
    verify_firebase_token,
)

User = get_user_model()

router = Router(tags=['Authentication'])

@router.post('/admin-login')
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
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@router.get('/device/approval-status')
def check_device_approval(request):
    """
    Check if the device/user is approved.
    Since the mobile app calls this endpoint to poll approval status,
    we inspect the Authorization header if present.
    """
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from apps.accounts.models import DeviceSession
    
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # If the user is approved, check if there's any approved device session
            is_approved = user.is_approved and DeviceSession.objects.filter(user=user, is_approved=True).exists()
            return {"success": True, "data": {"is_approved": is_approved}}
        except Exception:
            pass
            
    return {"success": True, "data": {"is_approved": False}}


@router.post('/firebase/login')
def firebase_auth(request, payload: FirebaseAuthSchema):
    """
    Authenticate with a Firebase ID token.
    Handles both Google Sign-In and Phone OTP flows.
    Returns JWT tokens on success, or a status string when approval is pending.
    """
    try:
        decoded = verify_firebase_token(payload.firebase_token)
    except FirebaseTokenError as e:
        raise HttpError(401, str(e))
    except FirebaseServiceUnavailableError as e:
        raise HttpError(503, str(e))

    response = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    if response.get("success") and payload.name:
        firebase_uid = decoded.get('uid')
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        if user and not user.first_name and not user.last_name:
            user.first_name = payload.name
            user.save(update_fields=['first_name'])
            if 'user' in response.get('data', {}):
                response['data']['user']['name'] = user.get_full_name() or user.username

    return response

@router.post('/send-otp')
def otp_request(request, payload: OtpRequestSchema):
    """
    Check if a phone number is registered before requesting OTP.
    """
    is_existing = User.objects.filter(phone_number=payload.phone).exists()
    return {
        "success": True,
        "data": {
            "is_existing_user": is_existing,
            "can_proceed": True,
        }
    }

@router.post('/otp/verify')
def otp_verify(request, payload: OtpVerifySchema):
    """
    Verify OTP with Firebase and authenticate.
    """
    try:
        decoded = verify_firebase_token(payload.id_token)
    except FirebaseTokenError as e:
        raise HttpError(401, str(e))
    except FirebaseServiceUnavailableError as e:
        raise HttpError(503, str(e))

    response = AuthService.authenticate(
        decoded_token=decoded,
        device_payload=payload.device,
    )

    if response.get("success") and payload.name:
        firebase_uid = decoded.get('uid')
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        if user and not user.first_name and not user.last_name:
            user.first_name = payload.name
            user.save(update_fields=['first_name'])
            if 'user' in response.get('data', {}):
                response['data']['user']['name'] = user.get_full_name() or user.username
                
    return response
