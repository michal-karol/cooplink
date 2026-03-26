from django.urls import path

from .views import (
    add_link,
    category_list_create,
    delete_link,
    edit_link,
    home,
    library_view,
    export_links_csv,
)

app_name = "links"

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", library_view, name="dashboard"),
    path("library/", library_view, name="library"),
    path("categories/", category_list_create, name="categories"),
    path("links/add/", add_link, name="add_link"),
    path("links/<int:pk>/edit/", edit_link, name="edit_link"),
    path("links/<int:pk>/delete/", delete_link, name="delete_link"),
    path("library/export/csv/", export_links_csv, name="export_links_csv"),
]