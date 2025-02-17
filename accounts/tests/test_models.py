from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserModelTest(TestCase):
    def test_str_returns_username(self):
        """The __str__ method should return the username."""
        user = User.objects.create_user(
            username="testuser",
            password="secret123",
            email="test@example.com"
        )
        self.assertEqual(str(user), "testuser")

    def test_contact_number_optional(self):
        """The contact_number field is optional."""
        # Create a user with a contact number.
        user_with_contact = User.objects.create_user(
            username="contactuser",
            password="secret123",
            email="contact@example.com",
            contact_number="1234567890"
        )
        self.assertEqual(user_with_contact.contact_number, "1234567890")

        # Create a user without a contact number.
        user_without_contact = User.objects.create_user(
            username="nocontractuser",
            password="secret123",
            email="nocontract@example.com"
        )
        self.assertIsNone(user_without_contact.contact_number)
