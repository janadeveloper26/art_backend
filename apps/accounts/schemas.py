from ninja import Schema


class DeviceSchema(Schema):
    device_id: str | None = None
    device_name: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    android_version: str | None = None
    platform: str | None = None
    fcm_token: str | None = None

    
class FirebaseAuthSchema(Schema):
    firebase_token: str
    name: str | None = None
    email: str | None = None
    avatar: str | None = None
    device: DeviceSchema | None = None

class AdminLoginSchema(Schema):
    username: str
    password: str

from datetime import datetime

class UserOutSchema(Schema):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    date_joined: datetime | None = None
    is_approved: bool

class OtpRequestSchema(Schema):
    phone_number: str
    phone: str | None = None  # backward-compat alias

class OtpVerifySchema(Schema):
    id_token: str
    name: str | None = None
    email: str | None = None
    avatar: str | None = None
    device: DeviceSchema | None = None

class UserStatsSchema(Schema):
    total_courses: int
    watch_time_hours: float
    completion_rate: int

class ProfileSchema(Schema):
    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str
    is_verified: bool
    stats: UserStatsSchema | None = None

class ProfileUpdateSchema(Schema):
    name: str | None = None
    email: str | None = None


class TokenRefreshIn(Schema):
    refresh_token: str