from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_register_new_user(self, mocked_turnstile):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "michal",
                "email": "michal@example.com",
                "password1": "CoopLink1337",
                "password2": "CoopLink1337",
                "cf-turnstile-response": "test-token",
            },
        )

        self.assertRedirects(response, reverse("links:dashboard"))
        self.assertTrue(User.objects.filter(username="michal").exists())

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_login_with_valid_credentials(self, mocked_turnstile):
        User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "michal",
                "password": "CoopLink1337",
                "cf-turnstile-response": "test-token",
            },
        )

        self.assertRedirects(response, reverse("links:dashboard"))

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="CoopLink1337",
        )

    def test_update_profile_details(self):
        self.client.force_login(self.user)

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
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Michal")
        self.assertEqual(self.user.last_name, "Nowak")
        self.assertEqual(self.user.email, "new@example.com")

    def test_change_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "action": "password",
                "old_password": "CoopLink1337",
                "new_password1": "CoopLinkNew1337",
                "new_password2": "CoopLinkNew1337",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        dashboard_response = self.client.get(reverse("links:dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)

        self.client.post(reverse("accounts:logout"))
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password="CoopLinkNew1337",
            )
        )
