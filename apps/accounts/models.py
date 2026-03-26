from django.contrib.auth.models import User
from django.db import models


class UserSecurity(models.Model):
    # One security profile per user
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="security",
    )
    # if True user must enter code sent by email 
    is_email_otp_enabled = models.BooleanField(default=False)
    # Store a hashed version of the current OTP code
    email_otp_code_hash = models.CharField(max_length=255, blank=True)
    # The current OTP code becomes invalid after X time (set in settings)
    email_otp_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Security settings for {self.user.username}"