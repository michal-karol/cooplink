from django.urls import path

from .views import add_link, dashboard, home

app_name = "links"

urlpatterns = [
    # Public landing page
    path("", home, name="home"),
    # Private page for logged-in users
    path("dashboard/", dashboard, name="dashboard"),
    # Page dor saving a new link
    path("links/add/", add_link, name="add_link"),
]
