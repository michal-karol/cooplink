from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, LinkForm
from .models import Category, Link


def home(request):
    if request.user.is_authenticated:
        return redirect("links:dashboard")
    return render(request, "links/home.html")


@login_required
def personal_dashboard(request):
    # Start with the current user's links only.
    user_links = Link.objects.filter(user=request.user).select_related("category")

    # Pinned links appear first on the dashboard.
    pinned_links = user_links.filter(is_pinned=True).order_by("-updated_at")
    recent_links = user_links.filter(is_pinned=False).order_by("-created_at")[:6]

    return render(
        request,
        "links/personal_dashboard.html",
        {
            "pinned_links": pinned_links,
            "recent_links": recent_links,
            "total_links": user_links.count(),
            "shared_links_count": user_links.filter(is_shared=True).count(),
            "pinned_links_count": pinned_links.count(),
        },
    )


@login_required
def shared_dashboard(request):
    # Shared links are visible to every logged-in user.
    links = Link.objects.filter(is_shared=True).select_related("category", "user")
    categories = Category.objects.all().order_by("name")

    query = request.GET.get("q", "").strip()
    if query:
        links = links.filter(
            Q(title__icontains=query)
            | Q(category__name__icontains=query)
            | Q(user__username__icontains=query)
        )

    selected_category = request.GET.get("category", "").strip()
    if selected_category.isdigit():
        links = links.filter(category_id=selected_category)

    paginator = Paginator(links, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "links/shared_dashboard.html",
        {
            "page_obj": page_obj,
            "categories": categories,
            "query": query,
            "selected_category": selected_category,
        },
    )


@login_required
def library_view(request):
    links = Link.objects.filter(user=request.user).select_related("category")
    categories = Category.objects.all().order_by("name")

    query = request.GET.get("q", "").strip()
    if query:
        links = links.filter(
            Q(title__icontains=query) | Q(category__name__icontains=query)
        )

    selected_category = request.GET.get("category", "").strip()
    if selected_category.isdigit():
        links = links.filter(category_id=selected_category)

    view_mode = request.GET.get("view", "cards")
    if view_mode not in {"cards", "list"}:
        view_mode = "cards"

    paginator = Paginator(links, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "links/library.html",
        {
            "page_obj": page_obj,
            "categories": categories,
            "query": query,
            "selected_category": selected_category,
            "view_mode": view_mode,
        },
    )


@login_required
def add_link(request):
    if request.method == "POST":
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            link.save()
            messages.success(request, "Link saved successfully.")
            return redirect("links:library")
    else:
        form = LinkForm()

    return render(
        request,
        "links/link_form.html",
        {
            "form": form,
            "page_title": "Save a link",
            "page_badge": "New link",
            "page_description": "Add a title, URL, notes, and choose whether the link should be shared.",
            "submit_label": "Save link",
        },
    )


@login_required
def edit_link(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, "Link updated successfully.")
            return redirect("links:library")
    else:
        form = LinkForm(instance=link)

    return render(
        request,
        "links/link_form.html",
        {
            "form": form,
            "page_title": "Edit link",
            "page_badge": "Update link",
            "page_description": "Change the details of a saved link, including whether it is shared.",
            "submit_label": "Save changes",
        },
    )


@login_required
def delete_link(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        link.delete()
        messages.success(request, "Link deleted successfully.")
        return redirect("links:library")

    return render(request, "links/link_confirm_delete.html", {"link": link})


@login_required
def toggle_pin(request, pk):
    # A user can only pin or unpin their own links.
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        link.is_pinned = not link.is_pinned
        link.save(update_fields=["is_pinned"])

        if link.is_pinned:
            messages.success(request, "Link pinned to your dashboard.")
        else:
            messages.success(request, "Link removed from your pinned links.")

    next_url = request.POST.get("next") or "links:dashboard"
    return redirect(next_url)


@login_required
def category_list_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("links:categories")
    else:
        form = CategoryForm()

    categories = Category.objects.all().order_by("name")
    return render(
        request,
        "links/categories.html",
        {
            "form": form,
            "categories": categories,
        },
    )