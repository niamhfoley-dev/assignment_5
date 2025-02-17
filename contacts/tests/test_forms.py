from django.test import TestCase
from django.contrib.auth import get_user_model
from contacts.forms import ContactForm

User = get_user_model()


class ContactFormTest(TestCase):
    def setUp(self):
        # Create two users: one will be the request user, the other a possible contact.
        self.request_user = User.objects.create_user(username="user1", password="pass")
        self.other_user = User.objects.create_user(username="user2", password="pass")

    def test_contact_user_queryset_excludes_request_user(self):
        """Ensure the contact_user queryset excludes the request user."""
        form = ContactForm(request_user=self.request_user)
        qs = form.fields['contact_user'].queryset
        self.assertNotIn(self.request_user, qs)
        self.assertIn(self.other_user, qs)

    def test_widget_attributes(self):
        """Ensure the widget attributes are set correctly."""
        form = ContactForm(request_user=self.request_user)

        # Check contact_user widget
        contact_user_widget_class = form.fields['contact_user'].widget.attrs.get('class', '')
        self.assertIn('form-select', contact_user_widget_class)

        # Check phone widget
        phone_widget_attrs = form.fields['phone'].widget.attrs
        self.assertIn('form-control', phone_widget_attrs.get('class', ''))
        self.assertEqual(phone_widget_attrs.get('placeholder'), 'Enter phone number')

        # Check note widget
        note_widget_attrs = form.fields['note'].widget.attrs
        self.assertIn('form-control', note_widget_attrs.get('class', ''))
        self.assertEqual(note_widget_attrs.get('rows'), 3)
        self.assertEqual(note_widget_attrs.get('placeholder'), 'Additional notes (optional)')

    def test_form_valid_data(self):
        """Test that the form is valid with correct data."""
        data = {
            'contact_user': self.other_user.pk,
            'phone': '123456789',
            'note': 'Test note',
        }
        form = ContactForm(data=data, request_user=self.request_user)
        self.assertTrue(form.is_valid(), form.errors)
