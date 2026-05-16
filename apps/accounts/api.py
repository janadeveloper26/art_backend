from ninja import Router
from .schemas import (
    FirebaseLoginSchema, RefreshTokenSchema, 
    AuthResponseData, UserSchema, OTPRequestSchema,
    OTPVerifySchema, DeviceMetadataSchema
)
from .models import User, UserStatus
from .services import AuthService
from core.responses import success_response, StandardResponse
from core.permissions import AuthBearer
from core.exceptions import APIError

router = Router()

@router.post("/otp/request", response={200: StandardResponse})
def request_otp(request, data: OTPRequestSchema):
    user = User.objects.filter(phone=data.phone).first()
    if user and user.status == UserStatus.BLOCKED:
        raise APIError(403, "This account has been blocked. Please contact support.")
    
    return success_response(data={
        "is_existing_user": user is not None,
        "can_proceed": True
    })

@router.get("/me", auth=AuthBearer(), response={200: StandardResponse})
def get_me(request):
    user_data = UserSchema.from_orm(request.auth)
    return success_response(data=user_data)

@router.post("/otp/verify", response={200: StandardResponse})
def otp_verify(request, data: OTPVerifySchema):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    
    user, device_obj, is_new_user = AuthService.firebase_login(
        data.id_token, 
        data.device.dict(),
        ip=ip,
        user_agent=user_agent
    )
    
    # If name was provided in verify payload, update it
    if data.name and not user.name:
        user.name = data.name
        user.save()
    
    access, refresh = AuthService.generate_tokens(user, device_obj, ip=ip, user_agent=user_agent)
    
    is_registration_complete = bool(user.name and user.skill_level)
    
    resp_data = {
        "access_token": access,
        "refresh_token": refresh,
        "is_new_user": is_new_user,
        "is_registration_complete": is_registration_complete,
        "user": UserSchema.from_orm(user)
    }
    return success_response(data=resp_data)

@router.post("/firebase/login", response={200: StandardResponse})
def firebase_login(request, data: FirebaseLoginSchema):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    
    user, device, is_new_user = AuthService.firebase_login(
        data.id_token, 
        data.device.dict(),
        ip=ip,
        user_agent=user_agent
    )
    
    access, refresh = AuthService.generate_tokens(user, device, ip=ip, user_agent=user_agent)
    
    is_registration_complete = bool(user.name and user.skill_level)
    
    resp_data = {
        "access_token": access,
        "refresh_token": refresh,
        "is_new_user": is_new_user,
        "is_registration_complete": is_registration_complete,
        "user": UserSchema.from_orm(user)
    }
    return success_response(data=resp_data)

@router.post("/refresh", response={200: StandardResponse})
def refresh_token(request, data: RefreshTokenSchema):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    
    access, refresh = AuthService.refresh_access_token(
        data.refresh_token,
        ip=ip,
        user_agent=user_agent
    )
    
    resp_data = {
        "access_token": access,
        "refresh_token": refresh
    }
    return success_response(data=resp_data)

@router.post("/logout", response={200: StandardResponse})
def logout(request, data: RefreshTokenSchema):
    AuthService.logout(data.refresh_token)
    return success_response(data={"message": "Logged out successfully"})
