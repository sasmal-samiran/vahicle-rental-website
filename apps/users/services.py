import random
from datetime import timedelta
from django.utils import timezone
from .models import OTPVerification, User

class OTPService:
    @staticmethod
    def generate_otp(identifier, purpose='LOGIN', user=None):
        # Invalidate existing active OTPs for same identifier & purpose
        OTPVerification.objects.filter(
            identifier=identifier,
            purpose=purpose,
            is_verified=False
        ).delete()

        # Generate a random 6-digit number
        otp_code = f'{random.randint(100000, 999999)}'
        expires_at = timezone.now() + timedelta(minutes=5)

        record = OTPVerification.objects.create(
            user=user,
            identifier=identifier,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=expires_at
        )

        return record

    @staticmethod
    def verify_otp(identifier, otp_code, purpose='LOGIN'):
        try:
            record = OTPVerification.objects.filter(
                identifier=identifier,
                purpose=purpose,
                is_verified=False
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            return False, 'No active OTP request found for this phone or email.'

        if record.is_expired():
            return False, 'OTP has expired. Please request a new one.'

        record.attempts += 1
        record.save(update_fields=['attempts'])

        if record.attempts > 5:
            return False, 'Maximum verification attempts exceeded. Please request a new OTP.'

        if record.otp_code != otp_code.strip():
            return False, 'Invalid verification code.'

        record.is_verified = True
        record.save(update_fields=['is_verified'])
        return True, 'OTP verified successfully.'
