from users.models import User
from authentication.dto.auth_dto import RegisterDTO, LoginDTO, ForgotPasswordDTO, VerifyOtpDTO, ResetPasswordDTO
from rest_framework_simplejwt.tokens import RefreshToken
from users.repository.user_repository import UserRepository
from dataclasses import asdict
import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

OTP_EXPIRY_SECONDS = 300  # 5 minutes

class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    def register_user(self, dto: RegisterDTO) -> tuple[bool, str, dict]:
        if User.objects.filter(email=dto.email).exists():
            return False, "Email already exists", {}
            
        user = User.objects.create_user(
            email=dto.email,
            password=dto.password,
            name=dto.name
        )
        
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        user_dto = self.user_repository.get_by_id(user.id)
        return True, "User registered successfully", {"user": asdict(user_dto), "tokens": tokens}

    def login_user(self, dto: LoginDTO) -> tuple[bool, str, dict]:
        try:
            user = User.objects.get(email=dto.email)
            if not user.check_password(dto.password):
                return False, "Invalid credentials", {}
                
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            user_dto = self.user_repository.get_by_id(user.id)
            return True, "Login successful", {"user": asdict(user_dto), "tokens": tokens}
        except User.DoesNotExist:
            return False, "User not found", {}

    def forgot_password(self, dto: ForgotPasswordDTO) -> tuple[bool, str, dict]:
        """Generate a 6-digit OTP, store in cache (5 min TTL), and email it.
        If a valid OTP already exists, resend the same one instead of generating a new one.
        This prevents the old OTP from being invalidated when the user clicks Resend.
        """
        if not User.objects.filter(email=dto.email).exists():
            # Security: don't reveal whether the email exists
            return True, "If this email exists, an OTP has been sent.", {}

        cache_key = f"otp:{dto.email}"

        # Reuse existing OTP if it's still valid — don't overwrite on resend
        existing_otp = cache.get(cache_key)
        otp = existing_otp if existing_otp else str(random.randint(100000, 999999))

        if not existing_otp:
            cache.set(cache_key, otp, timeout=OTP_EXPIRY_SECONDS)
            print(f"[OTP] New OTP generated for {dto.email}")
        else:
            print(f"[OTP] Resending existing OTP for {dto.email}")

        # ── Send email ───────────────────────────────────────────────────────
        subject = "Your OTP Code"
        message = (
            f"Hello,\n\n"
            f"Your One-Time Password (OTP) is:\n\n"
            f"  {otp}\n\n"
            f"This code is valid for 5 minutes. Do not share it with anyone.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"— The Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[dto.email],
                fail_silently=False,
            )
            print(f"[EMAIL] OTP sent to {dto.email}")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send OTP to {dto.email}: {e}")
            return True, "OTP generated (email delivery failed — check SMTP settings).", {"otp_debug": otp}

        return True, "OTP sent successfully. Check your email.", {}

    def verify_otp(self, dto: VerifyOtpDTO) -> tuple[bool, str, dict]:
        """Verify the OTP submitted by the user."""
        cache_key = f"otp:{dto.email}"
        stored_otp = cache.get(cache_key)

        if stored_otp is None:
            return False, "OTP has expired. Please request a new one.", {}

        if stored_otp != dto.otp:
            return False, "Invalid OTP. Please try again.", {}

        # OTP is correct — delete it so it can't be reused
        cache.delete(cache_key)
        # Mark email as verified in cache so reset-password step can proceed
        cache.set(f"otp_verified:{dto.email}", True, timeout=600)

        return True, "OTP verified successfully.", {"email": dto.email}

    def reset_password(self, dto: ResetPasswordDTO) -> tuple[bool, str, dict]:
        """Reset the user's password after OTP verification."""
        verified_key = f"otp_verified:{dto.email}"

        # Ensure the user completed the OTP step
        if not cache.get(verified_key):
            return False, "OTP verification required. Please verify your email first.", {}

        try:
            user = User.objects.get(email=dto.email)
        except User.DoesNotExist:
            return False, "User not found.", {}

        user.set_password(dto.new_password)
        user.save()

        # Invalidate the verified flag so it cannot be reused
        cache.delete(verified_key)

        print(f"[PASSWORD RESET] Password updated for {dto.email}")
        return True, "Password reset successfully. You can now log in.", {}
