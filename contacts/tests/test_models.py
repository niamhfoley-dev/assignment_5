from django.test import TestCase
from django.contrib.auth import get_user_model
from contacts.models import Contact

User = get_user_model()


class ContactModelTest(TestCase):
    def setUp(self):
        # Create two test users
        self.user1 = User.objects.create_user(
            username="user1", password="secret", first_name="John", last_name="Doe"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="secret", first_name="Alice", last_name="Smith"
        )

    def test_str_returns_full_name_or_username(self):
        """
        The __str__ method should return the contact user's full name if available,
        otherwise the username.
        """
        contact = Contact.objects.create(user=self.user1, contact_user=self.user2)
        expected_str = self.user2.get_full_name() or self.user2.username
        self.assertEqual(str(contact), expected_str)

        # Now remove the first and last name from user2, so __str__ returns username.
        self.user2.first_name = ""
        self.user2.last_name = ""
        self.user2.save()
        # Refresh the contact instance from the database
        contact.refresh_from_db()
        self.assertEqual(str(contact), self.user2.username)
