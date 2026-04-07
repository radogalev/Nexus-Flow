from django.test import TestCase

from accounts.models import CustomUser


class CustomUserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = CustomUser.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
            first_name="Jane",
            last_name="Doe",
        )
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(CustomUser.USERNAME_FIELD, "email")

    def test_full_name_property(self):
        user = CustomUser.objects.create_user(
            email="user2@example.com",
            password="StrongPass123!",
            first_name="John",
            last_name="Smith",
        )
        self.assertEqual(user.full_name, "John Smith")

    def test_create_superuser_sets_is_staff(self):
        user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="User",
        )
        self.assertTrue(user.is_staff)
