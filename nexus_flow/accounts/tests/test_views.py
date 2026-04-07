from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser


class AccountsViewTests(TestCase):
    @patch("accounts.views.send_welcome_email.delay")
    def test_register_creates_user(self, mock_delay):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "job_title": "Engineer",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(email="new@example.com").exists())
        self.assertTrue(mock_delay.called)

    @patch("accounts.views.send_welcome_email.delay")
    def test_register_duplicate_email_fails(self, mock_delay):
        CustomUser.objects.create_user(
            email="existing@test.com",
            password="StrongPass123!",
            first_name="Existing",
            last_name="User",
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "existing@test.com",
                "first_name": "New",
                "last_name": "User",
                "job_title": "Engineer",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("An account with this email already exists.", response.context["form"].errors.get("email", []))
        self.assertFalse(mock_delay.called)

    def test_profile_edit_requires_owner(self):
        owner = CustomUser.objects.create_user(
            email="owner@test.com", password="StrongPass123!", first_name="Owner", last_name="User"
        )
        other = CustomUser.objects.create_user(
            email="other@test.com", password="StrongPass123!", first_name="Other", last_name="User"
        )
        self.client.force_login(other)
        response = self.client.get(reverse("accounts:profile_edit", kwargs={"pk": owner.pk}))
        self.assertEqual(response.status_code, 403)
