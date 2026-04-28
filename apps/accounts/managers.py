from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, name=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('The Email or Phone must be set')
        
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, name=name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, name=name, password=password, **extra_fields)
