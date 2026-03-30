from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Link


class LinkTests(TestCase):
    def setUp(self):
        # Create users and shared categories before each test runs.
        self.user = User.objects.create_user(
            username="michal",
            password="CoopLink1337",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="CoopLink1337",
        )
        self.category = Category.objects.create(name="Research")
        self.other_category = Category.objects.create(name="Design")

    def test_logged_in_user_can_add_link(self):
        # Log the test user and see if link can be added 
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:add_link"),
            {
                "title": "Django",
                "url": "https://www.djangoproject.com/",
                "description": "Official Django website",
                "category": self.category.pk,
                "is_shared": "",
            },
        )

        # form should save the new link and redirect to the library
        self.assertRedirects(response, reverse("links:library"))
        self.assertTrue(Link.objects.filter(title="Django", user=self.user).exists())

    def test_logged_in_user_can_create_category(self):
        # Log in before posting to the category page.
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:categories"),
            {"name": "Tutorials"},
        )

        self.assertRedirects(response, reverse("links:categories"))
        self.assertTrue(Category.objects.filter(name="Tutorials").exists())

    def test_duplicate_category_name_is_rejected(self):
        # Try to create a duplicate category using different casing.
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:categories"),
            {"name": "research"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_library_search_finds_matching_link(self):
        # Create a link that should match the library search term.
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Django docs",
            url="https://docs.djangoproject.com/",
            description="Docs",
        )
        self.client.login(username="michal", password="CoopLink1337")

        # Search should return the matching link.
        response = self.client.get(reverse("links:library"), {"q": "django"})

        self.assertContains(response, "Django docs")

    def test_library_filter_by_category(self):
        # Create links in two different categories.
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
        self.client.login(username="michal", password="CoopLink1337")

        # Apply the category filter using the first category id.
        response = self.client.get(
            reverse("links:library"),
            {"category": str(self.category.pk)},
        )

        self.assertContains(response, "Research link")
        self.assertNotContains(response, "Design link")

    def test_owner_can_edit_link(self):
        # Create a link owned by the logged-in user.
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Old title",
            url="https://example.com/old",
            description="Old description",
        )
        self.client.login(username="michal", password="CoopLink1337")

        # Submit the edit form with new values, including shared status.
        response = self.client.post(
            reverse("links:edit_link", args=[link.pk]),
            {
                "title": "Updated title",
                "url": "https://example.com/new",
                "description": "Updated description",
                "category": self.other_category.pk,
                "is_shared": "on",
            },
        )

        # Refresh the object before checking the saved values.
        self.assertRedirects(response, reverse("links:library"))
        link.refresh_from_db()
        self.assertEqual(link.title, "Updated title")
        self.assertEqual(link.category, self.other_category)
        self.assertTrue(link.is_shared)

    def test_owner_can_delete_link(self):
        # Create a link that will be deleted.
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Delete me",
            url="https://example.com/delete",
            description="Delete this",
        )
        self.client.login(username="michal", password="CoopLink1337")

        # The delete POST should remove the row completely.
        response = self.client.post(reverse("links:delete_link", args=[link.pk]))

        self.assertRedirects(response, reverse("links:library"))
        self.assertFalse(Link.objects.filter(pk=link.pk).exists())

    def test_user_cannot_edit_another_users_link(self):
        # Create a link that belongs to a different user.
        link = Link.objects.create(
            user=self.other_user,
            category=self.category,
            title="Private",
            url="https://example.com/private",
            description="Private link",
        )
        self.client.login(username="michal", password="CoopLink1337")

        # The edit page should not be accessible to a non-owner.
        response = self.client.get(reverse("links:edit_link", args=[link.pk]))

        self.assertEqual(response.status_code, 404)

    def test_owner_can_pin_and_unpin_link(self):
        # Create one link that can be pinned and unpinned.
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Pin me",
            url="https://example.com/pin",
            description="Pin test",
        )
        self.client.login(username="michal", password="CoopLink1337")

        # First pin the link.
        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertRedirects(response, reverse("links:dashboard"))
        link.refresh_from_db()
        self.assertTrue(link.is_pinned)

        # Then unpin the same link.
        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertRedirects(response, reverse("links:dashboard"))
        link.refresh_from_db()
        self.assertFalse(link.is_pinned)

    def test_user_cannot_pin_another_users_link(self):
        # A user must not be able to pin or unpin someone else's link.
        link = Link.objects.create(
            user=self.other_user,
            category=self.category,
            title="Not yours",
            url="https://example.com/not-yours",
            description="Owned by another user",
        )
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:toggle_pin", args=[link.pk]),
            {"next": reverse("links:dashboard")},
        )

        self.assertEqual(response.status_code, 404)
        link.refresh_from_db()
        self.assertFalse(link.is_pinned)

    def test_shared_link_appears_on_shared_dashboard(self):
        # Create a shared link owned by the first user.
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Shared resource",
            url="https://example.com/shared",
            description="Shared link",
            is_shared=True,
        )
        self.client.login(username="other", password="CoopLink1337")

        # Another user should be able to see it on the shared dashboard.
        response = self.client.get(reverse("links:shared_dashboard"))

        self.assertContains(response, "Shared resource")
        self.assertContains(response, "Shared by michal")

    def test_private_link_does_not_appear_on_shared_dashboard(self):
        # Create a private link that should stay off the shared dashboard.
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Private resource",
            url="https://example.com/private",
            description="Private link",
            is_shared=False,
        )
        self.client.login(username="other", password="CoopLink1337")

        # Another user should not see the private link.
        response = self.client.get(reverse("links:shared_dashboard"))

        self.assertNotContains(response, "Private resource")

    def test_shared_dashboard_search_finds_matching_link(self):
        # Create a shared link that should match the search query.
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Design system",
            url="https://example.com/design-system",
            description="Shared design system",
            is_shared=True,
        )
        self.client.login(username="other", password="CoopLink1337")

        # Search on the shared dashboard should return the matching item.
        response = self.client.get(
            reverse("links:shared_dashboard"),
            {"q": "design"},
        )

        self.assertContains(response, "Design system")

    def test_shared_dashboard_filter_by_category(self):
        # Shared dashboard category filtering should only show matching links.
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
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.get(
            reverse("links:shared_dashboard"),
            {"category": str(self.category.pk)},
        )

        self.assertContains(response, "Research handbook")
        self.assertNotContains(response, "Design tokens")
