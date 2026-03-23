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

    def test_logged_in_user_can_update_profile(self):
        user = User.objects.create_user(
            username="michal",
            email="old@example.com",
            password="CoopLink1337",
        )
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "action": "profile",
                "first_name": "Michal",
                "last_name": "Nowak",
                "email": "new@example.com",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Michal")
        self.assertEqual(user.last_name, "Nowak")
        self.assertEqual(user.email, "new@example.com")

    def test_logged_in_user_can_change_password(self):
        User.objects.create_user(username="michal", password="CoopLink1337")
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "action": "password",
                "old_password": "CoopLink1337",
                "new_password1": "NewCoopLink1337",
                "new_password2": "NewCoopLink1337",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.client.logout()
        self.assertTrue(
        self.client.login(username="michal", password="NewCoopLink1337")
    )