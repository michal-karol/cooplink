from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

# Create your tests here.

class AccountTests(TestCase):
    def test_user_can_register(self):
        # Simulate a user submitting the registration form.
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "michal",
                "email": "michal@example.com",
                "password1": "CoopLink1337",
                "password2": "CoopLink1337",
            },
        )

        # After registration, the user should be redirected to dashboard
        self.assertRedirects(response, reverse("links:dashboard"))
        self.assertTrue(User.objects.filter(username="michal").exists())

    def test_user_can_login(self):
        # create a user in the test database.
        User.objects.create_user(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "michal",
                "password": "CoopLink1337",
            },
        )

        self.assertRedirects(response, reverse("links:dashboard"))
