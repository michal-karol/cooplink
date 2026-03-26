from django.contrib import admin

from .models import UserSecurity


@admin.register(UserSecurity)
class UserSecurityAdmin(admin.ModelAdmin):
    list_display = ("user", "is_email_otp_enabled", "email_otp_expires_at", "updated_at")
    search_fields = ("user__username", "user__email")
    list_filter = ("is_email_otp_enabled",)