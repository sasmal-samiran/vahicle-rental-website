from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import secrets

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number=None, email=None, password=None, **extra_fields):
        if not phone_number and not email:
            raise ValueError('Either Phone number or Email must be provided')
        if email:
            email = self.normalize_email(email)
        
        # If username not provided, generate one from phone or email
        if not extra_fields.get('username'):
            extra_fields['username'] = phone_number or (email.split('@')[0] + '_' + secrets.token_hex(3))
            
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username=username, email=email, password=password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('CUSTOMER', 'Customer'),
        ('ADMIN', 'Administrator'),
    )
    
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='CUSTOMER', db_index=True)
    driver_license_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_image_path = models.CharField(max_length=255, blank=True, null=True, help_text="Supabase Storage path, e.g. profiles/42/profile.jpg")
    is_phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    def __str__(self):
        name = self.get_full_name() or self.username
        return f'{name} ({self.role})'

    @property
    def profile_picture_url(self):
        from utils.supabase_storage import SupabaseStorageService
        return SupabaseStorageService.get_profile_image_url(self.profile_image_path)

    @property
    def is_admin_user(self):
        return self.role == 'ADMIN' or self.is_staff or self.is_superuser

class OTPVerification(models.Model):
    PURPOSE_CHOICES = (
        ('LOGIN', 'Login'),
        ('REGISTER', 'Registration'),
        ('VERIFY', 'Verification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='otps')
    identifier = models.CharField(max_length=100, db_index=True) # Phone or Email
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=15, choices=PURPOSE_CHOICES, default='LOGIN')
    attempts = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'OTP for {self.identifier} ({self.purpose})'
