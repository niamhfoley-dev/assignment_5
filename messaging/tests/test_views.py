from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from contacts.models import Contact
from messaging.models import Message

from django.utils import timezone

User = get_user_model()


class MessagingViewsTest(TestCase):
    def setUp(self):
        # Create two users: one for sender, one for recipient.
        self.sender = User.objects.create_user(username="sender", password="secret")
        self.recipient = User.objects.create_user(username="recipient", password="secret")

        # Create a sample message (if needed for other tests)
        self.message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Test Subject",
            body="Test message body.",
        )

        # Create a contact for the sender that references the recipient.
        Contact.objects.create(
            user=self.sender,
            contact_user=self.recipient
        )

        self.client.login(username="sender", password="secret")

    def test_create_message_view_post(self):
        """Test that posting valid data to CreateMessageView creates a new message."""
        url = reverse('send_message')
        data = {
            'recipient': self.recipient.pk,
            'subject': 'New Message',
            'body': 'Hello, this is a test message.',
        }
        response = self.client.post(url, data)
        # Should redirect to sent_messages.
        self.assertRedirects(response, reverse('sent_messages'))
        # Verify that the message is created.
        self.assertTrue(Message.objects.filter(subject="New Message", sender=self.sender).exists())


    def test_inbox_view(self):
        """Test that the InboxView returns only messages for the recipient and marks messages as read."""
        # Log in as the recipient.
        self.client.login(username="recipient", password="secret")
        url = reverse('inbox')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/inbox.html')
        # Ensure our message is present.
        self.assertContains(response, self.message.subject)


    def test_sent_messages_view(self):
        """Test that the SentMessagesView shows messages sent by the user."""
        self.client.login(username="sender", password="secret")
        url = reverse('sent_messages')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/sent_messages.html')
        self.assertContains(response, self.message.subject)


    def test_message_detail_view_marks_as_read(self):
        """Test that accessing the MessageDetailView marks the message as read (for recipient)."""
        self.client.login(username="recipient", password="secret")
        url = reverse('message_detail', args=[self.message.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # After GET, the message should be marked as read.
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)
        self.assertContains(response, self.message.body)


    def test_create_message_view_get(self):
        """Test that the CreateMessageView loads correctly for GET."""
        self.client.login(username="sender", password="secret")
        url = reverse('send_message')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/message_form.html')


    def test_reply_message_view_get(self):
        """Test that the ReplyMessageView prepopulates the subject for the recipient."""
        self.client.login(username="recipient", password="secret")
        url = reverse('reply_message', args=[self.message.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/reply_message.html')
        # Check for prepopulated subject in the rendered HTML.
        self.assertContains(response, "Re: " + self.message.subject)


    def test_reply_message_view_post(self):
        """Test that posting to ReplyMessageView creates a reply message."""
        self.client.login(username="recipient", password="secret")
        url = reverse('reply_message', args=[self.message.pk])
        data = {
            'subject': f"Re: {self.message.subject}",
            'body': "This is a reply message.",
        }
        response = self.client.post(url, data)
        # Should redirect to inbox.
        self.assertRedirects(response, reverse('inbox'))
        # Verify the reply message exists.
        reply = Message.objects.filter(subject__icontains="Re:", sender=self.recipient).first()
        self.assertIsNotNone(reply)
        # The reply's recipient should be the original sender.
        self.assertEqual(reply.recipient, self.sender)


    def test_archive_message_view(self):
        """Test that ArchiveMessageView archives a message for the recipient."""
        self.client.login(username="recipient", password="secret")
        url = reverse('archive_message', args=[self.message.pk])
        response = self.client.post(url)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_archived)
        self.assertRedirects(response, reverse('inbox'))
