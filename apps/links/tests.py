from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Link


class LinkTests(TestCase):
    def setUp(self):
        # Create a test user before each test runs.
        self.user = User.objects.create_user(
            username="michal",
            password="CoopLink1337",
        )

    def test_logged_in_user_can_add_link(self):
        # Log the test user and see if link can be added 
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:add_link"),
            {
                "title": "Django",
                "url": "https://www.djangoproject.com/",
                "description": "Official Django website",
                "category": "",
            },
        )

        # form should save the new link and redirect to the dashboard
        self.assertRedirects(response, reverse("links:dashboard"))
        self.assertTrue(Link.objects.filter(title="Django", user=self.user).exists())
