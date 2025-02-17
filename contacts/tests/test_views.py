from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from contacts.models import Contact

User = get_user_model()


class ContactsViewsTest(TestCase):
    def setUp(self):
        # Create two users. self.user is the logged-in user.
        self.user = User.objects.create_user(username='testuser', password='secret')
        self.other_user = User.objects.create_user(username='otheruser', password='secret')

        # Create a contact for self.user pointing to other_user.
        self.contact = Contact.objects.create(
            user=self.user,
            contact_user=self.other_user,
            phone='1234567890',
            note='Initial note'
        )

        # Log in as self.user.
        self.client.login(username='testuser', password='secret')

    def test_contact_list_view(self):
        """Test that ContactListView only shows contacts belonging to the logged-in user."""
        url = reverse('contacts:contact_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ensure our contact is in the list
        contacts = response.context['contacts']
        self.assertIn(self.contact, contacts)
        # And that we only see contacts for the logged-in user
        for contact in contacts:
            self.assertEqual(contact.user, self.user)

    def test_contact_create_view_get(self):
        """Test that the contact creation page loads correctly."""
        url = reverse('contacts:contact_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts/contact_form.html')

    def test_contact_create_view_post(self):
        """Test that posting valid data to the contact creation view creates a new contact."""
        url = reverse('contacts:contact_create')
        data = {
            'contact_user': self.other_user.pk,
            'phone': '9876543210',
            'note': 'New contact note',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('contacts:contact_list'))
        # Verify that a new contact has been created
        self.assertTrue(Contact.objects.filter(
            user=self.user,
            contact_user=self.other_user,
            phone='9876543210',
            note='New contact note'
        ).exists())

    def test_contact_detail_view(self):
        """Test that the detail view for a contact loads correctly."""
        url = reverse('contacts:contact_detail', args=[self.contact.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts/contact_detail.html')
        self.assertEqual(response.context['contact'], self.contact)

    def test_contact_update_view_get(self):
        """Test that the contact update page loads correctly."""
        url = reverse('contacts:contact_edit', args=[self.contact.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts/contact_form.html')

    def test_contact_update_view_post(self):
        """Test that updating a contact via the update view works correctly."""
        url = reverse('contacts:contact_edit', args=[self.contact.pk])
        data = {
            'contact_user': self.other_user.pk,
            'phone': '5555555555',
            'note': 'Updated note',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('contacts:contact_list'))
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.phone, '5555555555')
        self.assertEqual(self.contact.note, 'Updated note')
