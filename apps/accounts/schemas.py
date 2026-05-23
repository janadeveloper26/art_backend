from ninja import Schema


class DeviceSchema(Schema):
    device_id: str
    device_name: str
    manufacturer: str
    brand: str
    android_version: str
    platform: str
    fcm_token: str


class FirebaseAuthSchema(Schema):
    firebase_token: str
    device: DeviceSchema
