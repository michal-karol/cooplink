from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignUpForm


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