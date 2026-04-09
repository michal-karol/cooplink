import importlib
import inspect
from pathlib import Path

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Category, Link


class LinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="michal",
            email="michal@example.com",
            password="CoopLink1337",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="CoopLink1337",
        )
        self.category = Category.objects.create(name="Research")
        self.other_category = Category.objects.create(name="Design")

    def login(self, username="michal", password="CoopLink1337"):
        self.client.login(username=username, password=password)

    def test_add_link_with_valid_data(self):
        self.login()

        response = self.client.post(
            reverse("links:add_link"),
            {
                "title": "Django",
                "url": "https://www.djangoproject.com/",
                "description": "Official Django website",
                "category": self.category.pk,
            },
        )

        self.assertRedirects(response, reverse("links:library"))
        self.assertTrue(Link.objects.filter(title="Django", user=self.user).exists())

    def test_create_global_category(self):
        self.login()

        response = self.client.post(
            reverse("links:categories"),
            {"name": "Tutorials"},
        )

        self.assertRedirects(response, reverse("links:categories"))
        self.assertTrue(Category.objects.filter(name="Tutorials").exists())

        add_link_response = self.client.get(reverse("links:add_link"))
        self.assertContains(add_link_response, "Tutorials")

    def test_reject_duplicate_or_empty_category(self):
        self.login()

        empty_response = self.client.post(
            reverse("links:categories"),
            {"name": ""},
        )
        duplicate_response = self.client.post(
            reverse("links:categories"),
            {"name": "research"},
        )

        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, "This field is required.")
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertContains(duplicate_response, "already exists")

    def test_search_links_by_title_or_category(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Django docs",
            url="https://docs.djangoproject.com/",
            description="Docs",
        )
        Link.objects.create(
            user=self.user,
            category=self.other_category,
            title="Design system",
            url="https://example.com/design-system",
            description="Design",
        )
        self.login()

        response = self.client.get(reverse("links:library"), {"q": "django"})

        self.assertContains(response, "Django docs")
        self.assertNotContains(response, "Design system")

    def test_filter_links_by_category(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Research link",
            url="https://example.com/research",
            description="Research",
        )
        Link.objects.create(
            user=self.user,
            category=self.other_category,
            title="Design link",
            url="https://example.com/design",
            description="Design",
        )
        self.login()

        response = self.client.get(
            reverse("links:library"),
            {"category": str(self.category.pk)},
        )

        self.assertContains(response, "Research link")
        self.assertNotContains(response, "Design link")

    def test_edit_existing_link(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Old title",
            url="https://example.com/old",
            description="Old description",
        )
        self.login()

        response = self.client.post(
            reverse("links:edit_link", args=[link.pk]),
            {
                "title": "Updated title",
                "url": "https://example.com/new",
                "description": "Updated description",
                "category": self.other_category.pk,
            },
        )

        self.assertRedirects(response, reverse("links:library"))
        link.refresh_from_db()
        self.assertEqual(link.title, "Updated title")
        self.assertEqual(link.category, self.other_category)

        library_response = self.client.get(reverse("links:library"))
        self.assertContains(library_response, "Updated title")

    def test_delete_existing_link(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Delete me",
            url="https://example.com/delete",
            description="Delete this",
        )
        self.login()

        confirm_response = self.client.get(reverse("links:delete_link", args=[link.pk]))
        response = self.client.post(reverse("links:delete_link", args=[link.pk]))

        self.assertEqual(confirm_response.status_code, 200)
        self.assertRedirects(response, reverse("links:library"))
        self.assertFalse(Link.objects.filter(pk=link.pk).exists())

    def test_prevent_editing_another_users_link(self):
        link = Link.objects.create(
            user=self.other_user,
            category=self.category,
            title="Private",
            url="https://example.com/private",
            description="Private link",
        )
        self.login()

        response = self.client.get(reverse("links:edit_link", args=[link.pk]))

        self.assertEqual(response.status_code, 404)
        link.refresh_from_db()
        self.assertEqual(link.title, "Private")

    def test_open_personal_dashboard(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Dashboard link",
            url="https://example.com/dashboard",
            description="Shown on the dashboard",
        )
        self.login()

        response = self.client.get(reverse("links:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "links/personal_dashboard.html")
        self.assertContains(response, "Your important links")
        self.assertContains(response, "Saved links")

    def test_pin_link_to_dashboard(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Pin me",
            url="https://example.com/pin",
            description="Pin test",
        )
        self.login()

        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertRedirects(response, reverse("links:dashboard"))
        link.refresh_from_db()
        self.assertTrue(link.is_pinned)

        dashboard_response = self.client.get(reverse("links:dashboard"))
        pinned_links = list(dashboard_response.context["pinned_links"])
        self.assertEqual([item.pk for item in pinned_links], [link.pk])

    def test_unpin_link(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Pinned link",
            url="https://example.com/pinned",
            description="Pinned test",
            is_pinned=True,
        )
        self.login()

        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertRedirects(response, reverse("links:dashboard"))
        link.refresh_from_db()
        self.assertFalse(link.is_pinned)

        dashboard_response = self.client.get(reverse("links:dashboard"))
        self.assertEqual(list(dashboard_response.context["pinned_links"]), [])

    def test_mark_link_as_shared(self):
        self.login()

        response = self.client.post(
            reverse("links:add_link"),
            {
                "title": "Shared resource",
                "url": "https://example.com/shared",
                "description": "Shared link",
                "category": self.category.pk,
                "is_shared": "on",
            },
        )

        self.assertRedirects(response, reverse("links:library"))
        link = Link.objects.get(title="Shared resource", user=self.user)
        self.assertTrue(link.is_shared)

        library_response = self.client.get(reverse("links:library"))
        self.assertContains(library_response, "Shared")

        self.client.logout()
        self.login(username="other")
        shared_response = self.client.get(reverse("links:shared_dashboard"))
        self.assertContains(shared_response, "Shared resource")

    def test_mark_link_as_private(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Team link",
            url="https://example.com/team",
            description="Shared first",
            is_shared=True,
        )
        self.login()

        response = self.client.post(
            reverse("links:edit_link", args=[link.pk]),
            {
                "title": "Team link",
                "url": "https://example.com/team",
                "description": "Now private",
                "category": self.category.pk,
            },
        )

        self.assertRedirects(response, reverse("links:library"))
        link.refresh_from_db()
        self.assertFalse(link.is_shared)

        self.client.logout()
        self.login(username="other")
        shared_response = self.client.get(reverse("links:shared_dashboard"))
        self.assertNotContains(shared_response, "Team link")

    def test_view_shared_dashboard(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Shared resource",
            url="https://example.com/shared",
            description="Shared link",
            is_shared=True,
        )
        self.login(username="other")

        response = self.client.get(reverse("links:shared_dashboard"))

        self.assertContains(response, "Shared resource")
        self.assertContains(response, "Research")
        self.assertContains(response, "Shared by michal")

    def test_search_shared_links(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Django system",
            url="https://example.com/django-system",
            description="Shared django system",
            is_shared=True,
        )
        Link.objects.create(
            user=self.other_user,
            category=self.other_category,
            title="Backend notes",
            url="https://example.com/backend-notes",
            description="Private to search test",
            is_shared=True,
        )
        self.login()

        response = self.client.get(
            reverse("links:shared_dashboard"),
            {"q": "django"},
        )

        self.assertContains(response, "Django system")
        self.assertNotContains(response, "Backend notes")

    def test_filter_shared_links_by_category(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Research handbook",
            url="https://example.com/research-handbook",
            description="Research guide",
            is_shared=True,
        )
        Link.objects.create(
            user=self.other_user,
            category=self.other_category,
            title="Design tokens",
            url="https://example.com/design-tokens",
            description="Design guide",
            is_shared=True,
        )
        self.login()

        response = self.client.get(
            reverse("links:shared_dashboard"),
            {"category": str(self.category.pk)},
        )

        self.assertContains(response, "Research handbook")
        self.assertNotContains(response, "Design tokens")

    def test_prevent_pinning_another_users_link(self):
        link = Link.objects.create(
            user=self.other_user,
            category=self.category,
            title="Not yours",
            url="https://example.com/not-yours",
            description="Owned by another user",
        )
        self.login()

        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertEqual(response.status_code, 404)
        link.refresh_from_db()
        self.assertFalse(link.is_pinned)


class AutomatedCycleCoverageTests(SimpleTestCase):
    def test_cycle_suite_matches_documented_automated_cases(self):
        expected_tests = {
            "test_register_new_user",
            "test_login_with_valid_credentials",
            "test_update_profile_details",
            "test_change_password",
            "test_add_link_with_valid_data",
            "test_create_global_category",
            "test_reject_duplicate_or_empty_category",
            "test_search_links_by_title_or_category",
            "test_filter_links_by_category",
            "test_edit_existing_link",
            "test_delete_existing_link",
            "test_prevent_editing_another_users_link",
            "test_open_personal_dashboard",
            "test_pin_link_to_dashboard",
            "test_unpin_link",
            "test_mark_link_as_shared",
            "test_mark_link_as_private",
            "test_view_shared_dashboard",
            "test_search_shared_links",
            "test_filter_shared_links_by_category",
            "test_prevent_pinning_another_users_link",
        }

        discovered_tests = set()
        for module_name in ("apps.accounts.tests", "apps.links.tests"):
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, SimpleTestCase) or obj.__module__ != module_name:
                    continue
                if obj.__name__ == "AutomatedCycleCoverageTests":
                    continue

                for method_name, _ in inspect.getmembers(obj, inspect.isfunction):
                    if method_name.startswith("test_"):
                        discovered_tests.add(method_name)

        self.assertEqual(discovered_tests, expected_tests)
