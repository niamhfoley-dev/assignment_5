from django.test import TestCase
from django.contrib.auth import get_user_model
from messaging.models import Message

User = get_user_model()


class MessageModelTest(TestCase):
    def setUp(self):
        # Create two users for testing: one sender and one recipient.
        self.sender = User.objects.create_user(username="sender", password="secret")
        self.recipient = User.objects.create_user(username="recipient", password="secret")

    def test_message_creation(self):
        """Test that a message is created with the correct fields."""
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Hello World",
            body="This is a test message.",
        )
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.recipient, self.recipient)
        self.assertEqual(message.subject, "Hello World")
        self.assertEqual(message.body, "This is a test message.")
        self.assertFalse(message.is_read)
        self.assertFalse(message.is_archived)
        # Timestamp should be automatically set.
        self.assertIsNotNone(message.timestamp)

    def test_message_str(self):
        """Test that __str__ returns the expected string."""
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Hello World - Testing __str__",
            body="Test message body.",
        )
        expected_str = f"{message.subject[:50]}... from {self.sender.username}"
        self.assertEqual(str(message), expected_str)

    def test_message_reply_relationship(self):
        """Test that the reply relationship works as expected."""
        original = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Original Message",
            body="This is the original message.",
        )
        reply = Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            subject="Re: Original Message",
            body="This is the reply message.",
            reply_to=original,
        )
        # Check that reply.reply_to correctly points to the original.
        self.assertEqual(reply.reply_to, original)
        # And that the original message's replies include this reply.
        self.assertIn(reply, original.replies.all())
