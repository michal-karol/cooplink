from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    LoginPasswordForm,
    OTPCodeForm,
    ProfileForm,
    SecuritySettingsForm,
    SignUpForm,
)
from .security import (
    clear_email_otp,
    get_or_create_security_profile,
    send_email_otp_code,
    validate_turnstile,
    verify_email_otp_code,
)


PENDING_AUTH_SESSION_KEY = "pending_auth_user_id"


def mask_email(email):
    if not email or "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        visible_local = local[:1]
    else:
        visible_local = local[:2]
    return f"{visible_local}***@{domain}"


def register_view(request):
    # Logged users should not see the register page again 
    if request.user.is_authenticated:
        return redirect("links:dashboard")

    if request.method == "POST":
        
        # Load the user details 
        form = SignUpForm(request.POST)

        # Validate the Turnstile widget before creating the account
        turnstile_ok, turnstile_error = validate_turnstile(request)
        if not turnstile_ok:
            form.add_error(None, turnstile_error)

        if turnstile_ok and form.is_valid():
            user = form.save()
            # Every user gets a related security profile 
            security_profile = get_or_create_security_profile(user)
            security_profile.is_email_otp_enabled = form.cleaned_data["enable_email_otp"]
            security_profile.save(update_fields=["is_email_otp_enabled", "updated_at"])

            if security_profile.is_email_otp_enabled:
                # Dont log in yet but first store the user id and send the code
                request.session[PENDING_AUTH_SESSION_KEY] = user.pk
                send_email_otp_code(user)
                messages.info(
                    request,
                    "Your account was created. Enter the code we sent to your email to finish signing in.",
                )
                return redirect("accounts:otp_verify")

            # If email OTP is off can log the user stright away
            login(request, user)
            messages.success(request, "Your account has been created.")
            return redirect("links:dashboard")
    else:
        form = SignUpForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
    )


def login_view(request):
    # Logged users should go straight to the dashboard.
    if request.user.is_authenticated:
        return redirect("links:dashboard")

    if request.method == "POST":
        # validate username and password.
        form = LoginPasswordForm(request.POST, request=request)

        # Turnstile on the login page
        turnstile_ok, turnstile_error = validate_turnstile(request)
        if not turnstile_ok:
            form.add_error(None, turnstile_error)

        if turnstile_ok and form.is_valid():
            user = form.user
            security_profile = get_or_create_security_profile(user)

            if security_profile.is_email_otp_enabled:
                # Remember which user passed the password step
                request.session[PENDING_AUTH_SESSION_KEY] = user.pk
                send_email_otp_code(user)
                messages.info(request, "We sent a one-time code to your email address.")
                return redirect("accounts:otp_verify")

            # If OTP is disabled password login is enough 
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("links:dashboard")
    else:
        form = LoginPasswordForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
    )


def otp_verify_view(request):
    # verify the emailed code before logging in
    user_id = request.session.get(PENDING_AUTH_SESSION_KEY)
    if not user_id:
        messages.error(request, "Start from the login or registration page first.")
        return redirect("accounts:login")

    user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = OTPCodeForm(request.POST)
        if form.is_valid() and verify_email_otp_code(user, form.cleaned_data["otp_code"]):
            # The login is only completed after the code is correct
            login(request, user)
            request.session.pop(PENDING_AUTH_SESSION_KEY, None)
            messages.success(request, "You are now logged in.")
            return redirect("links:dashboard")

        if form.is_valid():
            form.add_error("otp_code", "That code is invalid or expired.")
    else:
        form = OTPCodeForm()

    return render(
        request,
        "accounts/otp_verify.html",
        {
            "form": form,
            "masked_email": mask_email(user.email),
        },
    )


def resend_otp_view(request):
    # user can request a new code if old one expired 
    user_id = request.session.get(PENDING_AUTH_SESSION_KEY)
    if not user_id:
        messages.error(request, "Start from the login or registration page first.")
        return redirect("accounts:login")

    user = get_object_or_404(User, pk=user_id)
    send_email_otp_code(user)
    messages.success(request, "A new code has been sent to your email.")
    return redirect("accounts:otp_verify")


@require_POST
def logout_view(request):
    # Clear any leftover OTP state before ending the session
    if request.user.is_authenticated:
        clear_email_otp(request.user)
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("links:home")


@login_required
def profile_view(request):
    # This page has three forms:
    # 1 - Profile details
    # 2 - Password change
    # 3 - Security settings
    security_profile = get_or_create_security_profile(request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
            security_form = SecuritySettingsForm(
                initial={"enable_email_otp": security_profile.is_email_otp_enabled}
            )

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("accounts:profile")

        elif action == "password":
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            security_form = SecuritySettingsForm(
                initial={"enable_email_otp": security_profile.is_email_otp_enabled}
            )

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been updated.")
                return redirect("accounts:profile")

        elif action == "security":
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
            security_form = SecuritySettingsForm(request.POST)

            if security_form.is_valid():
                security_profile.is_email_otp_enabled = security_form.cleaned_data["enable_email_otp"]
                security_profile.save(update_fields=["is_email_otp_enabled", "updated_at"])
                messages.success(request, "Your security settings have been updated.")
                return redirect("accounts:profile")

        else:
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
            security_form = SecuritySettingsForm(
                initial={"enable_email_otp": security_profile.is_email_otp_enabled}
            )
    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        security_form = SecuritySettingsForm(
            initial={"enable_email_otp": security_profile.is_email_otp_enabled}
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "security_form": security_form,
        },
    )
