from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import DeviceSession

User = get_user_model()


class AuthService:
    @staticmethod
    def authenticate(decoded_token, device_payload):
        firebase_uid = decoded_token.get('uid') or decoded_token.get('user_id') or decoded_token.get('sub')

        email = decoded_token.get('email', '')

        phone_number = decoded_token.get('phone_number', '')

        user, created = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'username': firebase_uid,
                'email': email,
                'phone_number': phone_number,
            },
        )

        # ------------------------------------------------------------------ #
        # Device handling (device_payload is optional for non-mobile callers) #
        # ------------------------------------------------------------------ #
        device = None
        if device_payload and device_payload.device_id:
            device, _ = DeviceSession.objects.get_or_create(
                user=user,
                device_id=device_payload.device_id,
                defaults={
                    'device_name': device_payload.device_name or '',
                    'manufacturer': device_payload.manufacturer or '',
                    'brand': device_payload.brand or '',
                    'android_version': device_payload.android_version or '',
                    'platform': device_payload.platform or '',
                    'fcm_token': device_payload.fcm_token or '',
                },
            )

            # Always refresh the FCM token
            device.fcm_token = device_payload.fcm_token or ''

            # If the user is already approved, auto-approve the device so the
            # user isn't blocked by a second approval gate after admin approval.
            if user.is_approved and not device.is_approved:
                device.is_approved = True
                device.approved_at = timezone.now()
                device.save(update_fields=['fcm_token', 'is_approved', 'approved_at', 'updated_at'])
            else:
                device.save(update_fields=['fcm_token', 'updated_at'])

        # ------------------------------------------------------------------ #
        # Approval gates — return pending status so API layer can 422         #
        # ------------------------------------------------------------------ #
        if not user.is_approved:
            return {
                'success': False,
                'pending': True,
                'status': 'pending_user_approval',
                'message': 'Your account is pending admin approval.',
            }

        # Only enforce device approval when a device was supplied
        if device and not device.is_approved:
            return {
                'success': False,
                'pending': True,
                'status': 'pending_device_approval',
                'message': 'This device is pending admin approval.',
            }

        # ------------------------------------------------------------------ #
        # Issue JWT tokens                                                     #
        # ------------------------------------------------------------------ #
        refresh = RefreshToken.for_user(user)

        return {
            'success': True,
            'pending': False,
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'is_new_user': created,
                'is_registration_complete': True,
                'user': {
                    'id': str(user.id),
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'phone': user.phone_number,
                    'avatar': user.avatar or None,
                    'role': 'admin' if user.is_staff else 'student',
                    'is_verified': user.is_approved,
                }
            }
        }
