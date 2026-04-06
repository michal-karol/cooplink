from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import UserSecurity


# Create your tests here.

class AccountTests(TestCase):
    @patch("apps.accounts.views.validate_turnstile", return_value=(False, "Please complete the security check."))
    def test_register_fails_without_turnstile(self, mocked_turnstile):
        # Simulate user submitting registration form without passing Turnstile
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "michal",
                "email": "michal@example.com",
                "password1": "CoopLink1337",
                "password2": "CoopLink1337",
            },
        )

        # The user should stay on the register page and account should not be created
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please complete the security check.")
        self.assertFalse(User.objects.filter(username="michal").exists())

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_register_without_email_otp_logs_user_in(self, mocked_turnstile):
        # Register user who wants email OTP disabled
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "michal",
                "email": "michal@example.com",
                "password1": "CoopLink1337",
                "password2": "CoopLink1337",
            },
        )

        # once registratered user should go straight to the dashboard
        self.assertRedirects(response, reverse("links:dashboard"))
        self.assertTrue(User.objects.filter(username="michal").exists())

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_register_with_email_otp_redirects_to_verify(self, mocked_turnstile):
        # Register user who chooses email OTP during registration
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "michal",
                "email": "michal@example.com",
                "password1": "CoopLink1337",
                "password2": "CoopLink1337",
                "enable_email_otp": "on",
                "cf-turnstile-response": "test-token",
            },
        )

        # should send an email and ask for the code before login 
        self.assertRedirects(response, reverse("accounts:otp_verify"))
        self.assertEqual(len(mail.outbox), 1)
        security = UserSecurity.objects.get(user__username="michal")
        self.assertTrue(security.is_email_otp_enabled)

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_login_without_email_otp_logs_in_directly(self, mocked_turnstile):
        # create a user in the test database.
        user = User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )
        UserSecurity.objects.create(user=user, is_email_otp_enabled=False)

        # Submit the normal login form
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "michal",
                "password": "CoopLink1337",
                "cf-turnstile-response": "test-token",
            },
        )

        # Users without email OTP enabled should be logged in immediately
        self.assertRedirects(response, reverse("links:dashboard"))

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    def test_login_with_email_otp_redirects_to_verify(self, mocked_turnstile):
        # create a user in the test database with email OTP enabled 
        user = User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )
        UserSecurity.objects.create(user=user, is_email_otp_enabled=True)

        # password step should succeed, but login should not finish 
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "michal",
                "password": "CoopLink1337",
                "cf-turnstile-response": "test-token",
            },
        )

        # user should be moved to verification page 
        self.assertRedirects(response, reverse("accounts:otp_verify"))
        self.assertEqual(len(mail.outbox), 1)

    @patch("apps.accounts.views.validate_turnstile", return_value=(True, None))
    @patch("apps.accounts.security.generate_email_otp_code", return_value="123456")
    def test_otp_verify_logs_user_in(self, mocked_code, mocked_turnstile):
        # Create a user who requires email OTP 
        user = User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )
        UserSecurity.objects.create(user=user, is_email_otp_enabled=True)

        # complete the password step so the app sends the code 
        self.client.post(
            reverse("accounts:login"),
            {
                "username": "michal",
                "password": "CoopLink1337",
                "cf-turnstile-response": "test-token",
            },
        )

        # Then submit the OTP step with the mock code
        response = self.client.post(
            reverse("accounts:otp_verify"),
            {"otp_code": "123456"},
        )

        # correct code should complete the login
        self.assertRedirects(response, reverse("links:dashboard"))

    def test_logged_in_user_can_update_profile(self):
        # create a user in the test database.
        user = User.objects.create_user(
            username="michal",
            email="old@example.com",
            password="CoopLink1337",
        )
        # force_login skips the login as this is for profile editing only test
        self.client.force_login(user)

        # Submit the profile form
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "action": "profile",
                "first_name": "Michal",
                "last_name": "Nowak",
                "email": "new@example.com",
            },
        )

        # saved values should be updated in db
        self.assertRedirects(response, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")

    def test_logged_in_user_can_enable_email_otp(self):
        # create a user in the test database with email OTP turned off
        user = User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )
        UserSecurity.objects.create(user=user, is_email_otp_enabled=False)
        # force_login 
        self.client.force_login(user)

        # Submit the security settings form
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "action": "security",
                "enable_email_otp": "on",
            },
        )

        # flag should now be turned on in the profile
        self.assertRedirects(response, reverse("accounts:profile"))
        security = UserSecurity.objects.get(user=user)
        self.assertTrue(security.is_email_otp_enabled)

    def test_password_reset_sends_email(self):
        # create a user in the test database with email address
        User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )

        # submit password reset form
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "michal@example.com"},
        )

        # django queues reset email and redirect to the confirmation
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
