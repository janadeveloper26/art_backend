from ninja import Router
from .schemas import (
    OTPRequestSchema, OTPVerifySchema, GoogleLoginSchema, 
    AuthResponseData, OTPRequestData, UserSchema
)
from .services import AuthService
from core.responses import success_response, StandardResponse
from core.permissions import AuthBearer
from core.exceptions import APIError
from core.idempotency import idempotent

router = Router()

@router.get("/me", auth=AuthBearer(), response={200: StandardResponse})
def get_me(request):
    user_data = UserSchema.from_orm(request.auth)
    return success_response(data=user_data, message="User profile fetched")

@router.post("/otp/request", response={200: StandardResponse})
@idempotent(timeout=60)
def request_otp(request, data: OTPRequestSchema):
    # In production, trigger SMS gateway
    # Mock response matching frontend
    mock_data = {
        "phone_number": data.phone,
        "session_id": "sess_" + data.phone[-10:],
        "is_existing_user": AuthService.check_user_exists(data.phone)
    }
    return success_response(data=mock_data, message="OTP sent successfully")

@router.post("/otp/verify", response={200: StandardResponse})
@idempotent(timeout=60)
def verify_otp(request, data: OTPVerifySchema):
    user, is_new_user = AuthService.verify_otp(data.phone, data.otp, data.name)
    access, refresh = AuthService.generate_tokens(user)
    
    # Check if registration is complete (name and skill_level set)
    is_registration_complete = bool(user.name and user.skill_level)
    
    resp_data = {
        "access_token": access,
        "refresh_token": refresh,
        "is_new_user": is_new_user,
        "is_registration_complete": is_registration_complete,
        "user": UserSchema.from_orm(user)
    }
    return success_response(data=resp_data, message="Login successful")

@router.post("/google", response={200: StandardResponse})
@idempotent(timeout=60)
def google_login(request, data: GoogleLoginSchema):
    user, is_new_user = AuthService.google_login(data.id_token)
    access, refresh = AuthService.generate_tokens(user)
    
    is_registration_complete = bool(user.name and user.skill_level)
    
    resp_data = {
        "access_token": access,
        "refresh_token": refresh,
        "is_new_user": is_new_user,
        "is_registration_complete": is_registration_complete,
        "user": UserSchema.from_orm(user)
    }
    return success_response(data=resp_data, message="Google sign-in successful")
