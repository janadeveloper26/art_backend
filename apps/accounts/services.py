import hashlib
import datetime
import uuid
import jwt
import structlog
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from .models import User, AuthIdentity, AuthProvider
from .firebase_service import FirebaseService
from devices.models import UserDevice, DeviceStatus
from user_sessions.models import Session
from audit.models import AuditLog
from core.exceptions import APIError

logger = structlog.get_logger("art_backend")

class AuthService:
    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_tokens(user, device, ip=None, user_agent=None):
        if not user.is_active:
            raise APIError(403, f"Account is in {user.status} state. Please contact administrator.")
        
        if device.status != DeviceStatus.APPROVED:
            logger.warning("login_denied_device_pending", user_id=str(user.id), device_id=str(device.id))
            raise APIError(403, "Device pending admin approval. Please contact administrator.")
        
        access_payload = {
            'user_id': str(user.id),
            'device_id': str(device.id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        
        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            'user_id': str(user.id),
            'device_id': str(device.id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh',
            'jti': refresh_jti
        }
        
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Save session
        Session.objects.create(
            user=user,
            device=device,
            refresh_token_hash=AuthService._hash_token(refresh_token),
            expires_at=timezone.now() + datetime.timedelta(days=30),
            ip_address=ip,
            user_agent=user_agent
        )
        
        # Log Audit
        AuditLog.objects.create(
            user=user,
            device=device,
            event="LOGIN_SUCCESS",
            ip_address=ip,
            user_agent=user_agent
        )
        
        logger.info("login_success", user_id=str(user.id), device_id=str(device.id), ip=ip)
        
        return access_token, refresh_token

    @staticmethod
    def firebase_login(id_token, device_data, ip=None, user_agent=None):
        decoded_token = FirebaseService.verify_token(id_token)
        
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        phone = decoded_token.get('phone_number')
        name = decoded_token.get('name', 'User')
        
        # Determine provider
        firebase_provider = decoded_token.get('firebase', {}).get('sign_in_provider')
        provider = AuthProvider.GOOGLE if firebase_provider == 'google.com' else AuthProvider.OTP

        with transaction.atomic():
            # Identity Resolution Strategy:
            # 1. Existing provider UID
            identity = AuthIdentity.objects.filter(provider_uid=uid).first()
            user = identity.user if identity else None

            # 2. Verified phone number
            if not user and phone:
                user = User.objects.filter(phone=phone).first()
            
            # 3. Verified email address
            if not user and email:
                user = User.objects.filter(email=email).first()

            is_new_user = False
            if not user:
                is_new_user = True
                user = User.objects.create(
                    email=email,
                    phone=phone,
                    name=name
                )
            
            # Link the Firebase UID if not already linked
            if not identity:
                AuthIdentity.objects.create(
                    user=user,
                    provider=provider,
                    provider_uid=uid,
                    verified=True
                )
            
            # Device Verification
            device, created = UserDevice.objects.get_or_create(
                install_id=device_data['install_id'],
                defaults={
                    'user': user,
                    'platform': device_data['platform'],
                    'device_model': device_data.get('device_model'),
                    'os_version': device_data.get('os_version'),
                    'fcm_token': device_data.get('fcm_token'),
                    'app_version': device_data.get('app_version'),
                }
            )
            
            if not created:
                # Update metadata
                device.fcm_token = device_data.get('fcm_token', device.fcm_token)
                device.app_version = device_data.get('app_version', device.app_version)
                device.last_login_at = timezone.now()
                device.save()
            
            return user, device, is_new_user

    @staticmethod
    def refresh_access_token(refresh_token, ip=None, user_agent=None):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                raise APIError(401, "Invalid refresh token")
            
            token_hash = AuthService._hash_token(refresh_token)
            session = Session.objects.filter(
                refresh_token_hash=token_hash, 
                revoked_at__isnull=True,
                expires_at__gt=timezone.now()
            ).first()
            
            if not session:
                raise APIError(401, "Refresh token has been revoked or expired")
            
            user = session.user
            device = session.device
            
            if not user.is_active:
                raise APIError(403, "User account is disabled")
            
            # Revoke old session (Rotation)
            session.revoked_at = timezone.now()
            session.save()
            
            # Log Audit
            AuditLog.objects.create(
                user=user,
                device=device,
                event="TOKEN_REFRESH",
                ip_address=ip,
                user_agent=user_agent
            )
            
            logger.info("token_refresh_success", user_id=str(user.id), device_id=str(device.id))
            
            return AuthService.generate_tokens(user, device, ip, user_agent)
        except jwt.ExpiredSignatureError:
            raise APIError(401, "Refresh token expired")
        except Exception as e:
            raise APIError(401, f"Invalid refresh token: {str(e)}")

    @staticmethod
    def logout(refresh_token):
        token_hash = AuthService._hash_token(refresh_token)
        Session.objects.filter(refresh_token_hash=token_hash).update(revoked_at=timezone.now())
