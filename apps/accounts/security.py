import random
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import UserSecurity


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def get_or_create_security_profile(user):
    profile, created = UserSecurity.objects.get_or_create(user=user)
    return profile


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def validate_turnstile(request):
    # Registration and password login are protected by a required Turnstile check.
    token = request.POST.get("cf-turnstile-response", "").strip()

    if not token:
        return False, "Please complete the security check."

    if not settings.TURNSTILE_SECRET_KEY:
        return False, "Turnstile is required but not configured."

    try:
        response = requests.post(
            TURNSTILE_VERIFY_URL,
            data={
                "secret": settings.TURNSTILE_SECRET_KEY,
                "response": token,
                "remoteip": get_client_ip(request),
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return False, "The security check could not be completed. Please try again."

    if payload.get("success"):
        return True, None

    return False, "Security verification failed. Please try again."


def generate_email_otp_code():
    # Generate a 6-digit code
    return f"{random.randint(0, 999999):06d}"


def send_email_otp_code(user):
    profile = get_or_create_security_profile(user)
    code = generate_email_otp_code()
    expires_at = timezone.now() + timedelta(minutes=settings.EMAIL_OTP_EXPIRES_MINUTES)

    # only the hashed value in db
    profile.email_otp_code_hash = make_password(code)
    profile.email_otp_expires_at = expires_at
    profile.save(update_fields=["email_otp_code_hash", "email_otp_expires_at", "updated_at"])

    send_mail(
        subject="Your CoopLink verification code",
        message=(
            f"Your CoopLink verification code is: {code}\n\n"
            f"This code expires in {settings.EMAIL_OTP_EXPIRES_MINUTES} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def verify_email_otp_code(user, code):
    profile = get_or_create_security_profile(user)

    if not profile.email_otp_code_hash or not profile.email_otp_expires_at:
        return False

    if timezone.now() > profile.email_otp_expires_at:
        return False

    if not check_password(code, profile.email_otp_code_hash):
        return False

    # Clear the code after use so it can be used only once
    profile.email_otp_code_hash = ""
    profile.email_otp_expires_at = None
    profile.save(update_fields=["email_otp_code_hash", "email_otp_expires_at", "updated_at"])
    return True


def clear_email_otp(user):
    profile = get_or_create_security_profile(user)
    profile.email_otp_code_hash = ""
    profile.email_otp_expires_at = None
    profile.save(update_fields=["email_otp_code_hash", "email_otp_expires_at", "updated_at"])
