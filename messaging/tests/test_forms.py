from django.test import TestCase
from django.contrib.auth import get_user_model
from messaging.forms import MessageForm, ReplyMessageForm
from contacts.models import Contact

User = get_user_model()


class MessageFormTest(TestCase):
    def setUp(self):
        # Create two users: one for the request user and one for a potential recipient.
        self.request_user = User.objects.create_user(
            username='sender', password='secret', email='sender@example.com'
        )
        self.recipient_user = User.objects.create_user(
            username='recipient', password='secret', email='recipient@example.com'
        )
        # Create a contact so that request_user has recipient_user in contacts.
        self.contact = Contact.objects.create(
            user=self.request_user,
            contact_user=self.recipient_user,
            phone='1234567890',
            note='Test note'
        )

    def test_recipient_queryset_excludes_non_contacts(self):
        """
        Ensure that the MessageForm limits the recipient queryset to the request_user's contacts.
        """
        form = MessageForm(user=self.request_user)
        qs = form.fields['recipient'].queryset
        # The queryset should contain the recipient_user because they're in the request_user's contacts.
        self.assertIn(self.recipient_user, qs)
        # If we create another user not in contacts, they should not be included.
        another_user = User.objects.create_user(
            username='another', password='secret', email='another@example.com'
        )
        self.assertNotIn(another_user, qs)

    def test_widget_attributes_message_form(self):
        """Test that the widgets in MessageForm have the expected attributes."""
        form = MessageForm(user=self.request_user)
        recipient_attrs = form.fields['recipient'].widget.attrs
        self.assertIn('form-select', recipient_attrs.get('class', ''))
        self.assertEqual(recipient_attrs.get('data-placeholder'), 'Search or select a contact...')

        subject_attrs = form.fields['subject'].widget.attrs
        self.assertIn('form-control', subject_attrs.get('class', ''))
        self.assertEqual(subject_attrs.get('placeholder'), 'Enter subject...')

        body_attrs = form.fields['body'].widget.attrs
        self.assertIn('form-control', body_attrs.get('class', ''))
        self.assertEqual(body_attrs.get('placeholder'), 'Type your message here...')
        self.assertEqual(body_attrs.get('rows'), '5')

    def test_message_form_valid_data(self):
        """Test that MessageForm is valid with proper data."""
        data = {
            'recipient': self.recipient_user.pk,
            'subject': 'Test Subject',
            'body': 'Test message body',
        }
        form = MessageForm(data=data, user=self.request_user)
        self.assertTrue(form.is_valid(), form.errors)


class ReplyMessageFormTest(TestCase):
    def test_reply_message_form_widget_attributes(self):
        """Test that the ReplyMessageForm's widgets have the expected attributes."""
        form = ReplyMessageForm()
        subject_attrs = form.fields['subject'].widget.attrs
        self.assertIn('form-control', subject_attrs.get('class', ''))
        self.assertEqual(subject_attrs.get('placeholder'), 'Subject')

        body_attrs = form.fields['body'].widget.attrs
        self.assertIn('form-control', body_attrs.get('class', ''))
        self.assertEqual(body_attrs.get('placeholder'), 'Type your reply here...')
        self.assertEqual(body_attrs.get('rows'), '5')

    def test_reply_message_form_valid(self):
        """Test that ReplyMessageForm is valid with proper data."""
        data = {
            'subject': 'Re: Original Subject',
            'body': 'This is a reply message.',
        }
        form = ReplyMessageForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
