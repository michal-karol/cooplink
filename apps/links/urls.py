from django.urls import path

from .views import (
    add_link,
    category_list_create,
    delete_link,
    edit_link,
    home,
    library_view,
    personal_dashboard,
    shared_dashboard,
    toggle_pin,
)

app_name = "links"

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", personal_dashboard, name="dashboard"),
    path("library/", library_view, name="library"),
    path("shared/", shared_dashboard, name="shared_dashboard"),
    path("categories/", category_list_create, name="categories"),
    path("links/add/", add_link, name="add_link"),
    path("links/<int:pk>/edit/", edit_link, name="edit_link"),
    path("links/<int:pk>/delete/", delete_link, name="delete_link"),
    path("links/<int:pk>/toggle-pin/", toggle_pin, name="toggle_pin"),
]