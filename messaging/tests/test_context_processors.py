from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from messaging.context_processors import unread_messages_count
from messaging.models import Message

User = get_user_model()


class UnreadMessagesCountContextProcessorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create two users: one for sender and one for recipient.
        self.recipient = User.objects.create_user(username='recipient', password='secret')
        self.sender = User.objects.create_user(username='sender', password='secret')

    def test_unread_messages_count_for_authenticated_user(self):
        # Create two unread messages for the recipient.
        Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Test Message 1",
            body="Hello",
            is_archived=False,
            is_read=False,
        )
        Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Test Message 2",
            body="Hello again",
            is_archived=False,
            is_read=False,
        )

        request = self.factory.get('/')
        request.user = self.recipient

        context = unread_messages_count(request)
        self.assertEqual(context['unread_messages_count'], 2)

    def test_unread_messages_count_for_authenticated_user_with_no_unread(self):
        # Create a read message
        Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject="Read Message",
            body="All good",
            is_archived=False,
            is_read=True,
        )

        request = self.factory.get('/')
        request.user = self.recipient

        context = unread_messages_count(request)
        self.assertEqual(context['unread_messages_count'], 0)

    def test_unread_messages_count_for_anonymous_user(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()

        context = unread_messages_count(request)
        self.assertEqual(context['unread_messages_count'], 0)
