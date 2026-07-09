import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser

class AuthService:
    """
    Service layer containing core business logic for generating secure OTP keys,
    verifying verification tokens, and dispatching transaction alerts.
    """

    @staticmethod
    def generate_otp() -> str:
        """
        Generates a secure 6-digit numeric OTP string.
        """
        return f"{random.randint(100000, 999999)}"

    @classmethod
    def set_user_otp(cls, user: CustomUser) -> str:
        """
        Sets a fresh OTP code for the user along with a expiration timestamp (10 minutes).
        """
        otp = cls.generate_otp()
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])
        return otp

    @staticmethod
    def verify_user_otp(user: CustomUser, code: str) -> bool:
        """
        Verifies if the provided OTP code matches and is under 10 minutes old.
        """
        if not user.otp_code or user.otp_code != code:
            return False
            
        # Check OTP age (must be under 10 minutes)
        if timezone.now() > user.otp_created_at + timedelta(minutes=10):
            return False
            
        # Clean OTP codes on successful matching
        user.otp_code = ''
        user.otp_created_at = None
        user.save(update_fields=['otp_code', 'otp_created_at'])
        return True

    @staticmethod
    def send_verification_email(user: CustomUser, otp: str):
        """
        Sends verification link/code email using Django's email backend.
        """
        subject = 'PrepAI Account Verification'
        message = (
            f"Hello {user.first_name or 'Developer'},\n\n"
            f"Thank you for registering on PrepAI. Please verify your email using the following OTP code:\n\n"
            f"Verification Code: {otp}\n\n"
            f"This code will expire in 10 minutes.\n\n"
            f"Best regards,\nPrepAI Support"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )

    @staticmethod
    def send_password_reset_email(user: CustomUser, otp: str):
        """
        Sends recovery OTP code email using Django's email backend.
        """
        subject = 'PrepAI Password Reset OTP'
        message = (
            f"Hello {user.first_name or 'Developer'},\n\n"
            f"We received a request to recover your credentials on PrepAI. "
            f"Input the following 6-digit OTP code to reset your account password:\n\n"
            f"Security Code: {otp}\n\n"
            f"This code will expire in 10 minutes.\n\n"
            f"If you did not request this recovery, please ignore this email.\n\n"
            f"Best regards,\nPrepAI Support"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
