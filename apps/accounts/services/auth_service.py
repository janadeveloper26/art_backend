from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import DeviceSession

User = get_user_model()


class AuthService:
    @staticmethod
    def authenticate(decoded_token, device_payload):
        firebase_uid = decoded_token['uid']

        email = decoded_token.get('email', '')

        phone_number = decoded_token.get('phone_number', '')

        user, _ = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'username': firebase_uid,
                'email': email,
                'phone_number': phone_number,
            },
        )

        device, _ = DeviceSession.objects.get_or_create(
            user=user,
            device_id=device_payload.device_id,
            defaults={
                'device_name': device_payload.device_name,
                'manufacturer': device_payload.manufacturer,
                'brand': device_payload.brand,
                'android_version': device_payload.android_version,
                'platform': device_payload.platform,
                'fcm_token': device_payload.fcm_token,
            },
        )

        device.fcm_token = device_payload.fcm_token

        device.save(update_fields=['fcm_token', 'updated_at'])

        if not user.is_approved:
            return {
                'status': 'pending_user_approval',
            }

        if not device.is_approved:
            return {
                'status': 'pending_device_approval',
            }

        refresh = RefreshToken.for_user(user)

        return {
            'status': 'approved',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
