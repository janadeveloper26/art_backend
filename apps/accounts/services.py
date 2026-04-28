import jwt
import datetime
from django.conf import settings
from django.db import transaction
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User, AuthIdentity, AuthProvider
from core.exceptions import APIError

class AuthService:
    @staticmethod
    def generate_tokens(user):
        access_payload = {
            'user_id': str(user.id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        refresh_payload = {
            'user_id': str(user.id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return access_token, refresh_token

    @staticmethod
    def check_user_exists(phone):
        return User.objects.filter(phone=phone).exists()

    @staticmethod
    def verify_otp(phone, otp, name=None):
        if otp != "123456":
            raise APIError(400, "Invalid OTP")
        
        with transaction.atomic():
            user = User.objects.filter(phone=phone).first()
            is_new_user = False
            if not user:
                is_new_user = True
                user = User.objects.create(phone=phone, name=name or "New User")
            
            identity, created = AuthIdentity.objects.get_or_create(
                provider=AuthProvider.OTP,
                provider_uid=phone,
                defaults={'user': user, 'verified': True}
            )
            
            if not created:
                identity.verified = True
                identity.save()
            
            return user, is_new_user

    @staticmethod
    def google_login(token_id):
        try:
            idinfo = id_token.verify_oauth2_token(token_id, google_requests.Request())
            
            email = idinfo['email']
            google_uid = idinfo['sub']
            name = idinfo.get('name', '')

            with transaction.atomic():
                user = User.objects.filter(email=email).first()
                is_new_user = False
                
                if not user:
                    is_new_user = True
                    identity = AuthIdentity.objects.filter(provider=AuthProvider.GOOGLE, provider_uid=google_uid).first()
                    if identity:
                        user = identity.user
                        is_new_user = False
                    else:
                        user = User.objects.create(email=email, name=name)
                
                AuthIdentity.objects.get_or_create(
                    provider=AuthProvider.GOOGLE,
                    provider_uid=google_uid,
                    defaults={'user': user, 'verified': True}
                )
                
                return user, is_new_user

        except ValueError:
            raise APIError(400, "Invalid Google Token")
