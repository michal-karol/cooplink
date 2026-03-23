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
                "category": "",
            },
        )

        # form should save the new link and redirect to the library
        self.assertRedirects(response, reverse("links:library"))
        self.assertTrue(Link.objects.filter(title="Django", user=self.user).exists())


    def test_logged_in_user_can_create_category(self):
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:categories"),
            {"name": "Tutorials"},
        )

        self.assertRedirects(response, reverse("links:categories"))
        self.assertTrue(Category.objects.filter(name="Tutorials").exists())

    def test_duplicate_category_name_is_rejected(self):
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(
            reverse("links:categories"),
            {"name": "research"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_library_search_finds_matching_link(self):
        Link.objects.create(
            user=self.user,
            category=self.category,
            title="Django docs",
            url="https://docs.djangoproject.com/",
            description="Docs",
        )
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.get(reverse("links:library"), {"q": "django"})

        self.assertContains(response, "Django docs")

    def test_library_filter_by_category(self):
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

        response = self.client.get(
            reverse("links:library"),
            {"category": str(self.category.pk)},
        )

        self.assertContains(response, "Research link")
        self.assertNotContains(response, "Design link")

    def test_owner_can_edit_link(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Old title",
            url="https://example.com/old",
            description="Old description",
        )
        self.client.login(username="michal", password="CoopLink1337")

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

    def test_owner_can_delete_link(self):
        link = Link.objects.create(
            user=self.user,
            category=self.category,
            title="Delete me",
            url="https://example.com/delete",
            description="Delete this",
        )
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.post(reverse("links:delete_link", args=[link.pk]))

        self.assertRedirects(response, reverse("links:library"))
        self.assertFalse(Link.objects.filter(pk=link.pk).exists())

    def test_user_cannot_edit_another_users_link(self):
        link = Link.objects.create(
            user=self.other_user,
            category=self.category,
            title="Private",
            url="https://example.com/private",
            description="Private link",
        )
        self.client.login(username="michal", password="CoopLink1337")

        response = self.client.get(reverse("links:edit_link", args=[link.pk]))

        self.assertEqual(response.status_code, 404)
