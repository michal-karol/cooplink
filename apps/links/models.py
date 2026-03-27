from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models


class Category(models.Model):
    # Categories are global and shared by the whole app and all users can use them
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Link(models.Model):
    # Links belongs to the user who created it
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="links")
    category = models.ForeignKey(
        Category,
        # If a category is deleted, keep the link but remove the category
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="links",
    )
    title = models.CharField(max_length=200)
    url = models.URLField(validators=[URLValidator()])
    description = models.TextField(blank=True)
    # Shared links appear on the shared dashboard for all users.
    is_shared = models.BooleanField(default=False)
    # Pinned links appear first on the owner's personal dashboard.
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Newest links first on the dashboard.
        ordering = ["-created_at"]

    def __str__(self):
        return self.title