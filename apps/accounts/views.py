from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

from .forms import ProfileForm, SignUpForm

def register_view(request):
    # If the user is logged in redirect to dashboard
    if request.user.is_authenticated:
        return redirect("links:dashboard")

    if request.method == "POST":
        # check the data and create account
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in straight away after registratering
            login(request, user)
            messages.success(request, "Your account has been created.")
            return redirect("links:dashboard")
    else:
        # show empty form if its user firs visit
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    # This page have two forms:
    # 1 - Profile details
    # 2 - Password change
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(user=request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("accounts:profile")

        elif action == "password":
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user, data=request.POST)

            if password_form.is_valid():
                user = password_form.save()
                # Keep the user logged in after changing password.
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been updated.")
                return redirect("accounts:profile")

        else:
            # Fall back if the form action is missing or invalid.
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )