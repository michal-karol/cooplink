from django.contrib import admin

from .models import Category, Link


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    # filters and search for data 
    list_display = ("title", "user", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "url", "user__username")