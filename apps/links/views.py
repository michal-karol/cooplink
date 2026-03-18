from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LinkForm
from .models import Link


def home(request):
    # Signed-in users go straight to their dashboard.
    if request.user.is_authenticated:
        return redirect("links:dashboard")
    return render(request, "links/home.html")


@login_required
def dashboard(request):
    # Only load links that belong to the current user
    links = Link.objects.filter(user=request.user).select_related("category")
    return render(request, "links/dashboard.html", {"links": links})


@login_required
def add_link(request):
    # page to create a new link
    if request.method == "POST":
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            link.save()
            messages.success(request, "Link saved successfully.")
            return redirect("links:dashboard")
    else:
        form = LinkForm()

    return render(request, "links/link_form.html", {"form": form})
