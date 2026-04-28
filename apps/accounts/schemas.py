from typing import Optional
from ninja import Schema
from pydantic import EmailStr
from uuid import UUID

class OTPRequestSchema(Schema):
    phone: str

class OTPRequestData(Schema):
    phone_number: str
    session_id: str
    is_existing_user: bool

class OTPVerifySchema(Schema):
    phone: str
    otp: str
    name: Optional[str] = None

class GoogleLoginSchema(Schema):
    id_token: str

class UserSchema(Schema):
    id: UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = "assets/images/profile_avatar.png"
    role: str = "user"
    is_verified: bool = True

class AuthResponseData(Schema):
    access_token: str
    refresh_token: str
    is_new_user: bool
    is_registration_complete: bool
    user: UserSchema
