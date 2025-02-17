from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.forms import ProjectForm, ProjectTaskForm
from projects.models import Project, ProjectTask
from contacts.models import Contact

User = get_user_model()


class ProjectFormTest(TestCase):
    def setUp(self):
        # Create a test user and some contacts.
        self.user = User.objects.create_user(
            username="testuser", password="secret", email="test@example.com"
        )
        self.contact1 = Contact.objects.create(
            user=self.user,
            contact_user=User.objects.create_user(username="contact1", password="secret")
        )
        self.contact2 = Contact.objects.create(
            user=self.user,
            contact_user=User.objects.create_user(username="contact2", password="secret")
        )

    def test_stakeholders_queryset(self):
        """ProjectForm should restrict the stakeholders queryset to user's contacts."""
        form = ProjectForm(user=self.user)
        qs = form.fields['stakeholders'].queryset
        self.assertIn(self.contact1, qs)
        self.assertIn(self.contact2, qs)
        # Ensure that no other contacts are included.
        all_contacts = Contact.objects.all()
        for contact in all_contacts:
            if contact.user != self.user:
                self.assertNotIn(contact, qs)

    def test_stakeholders_widget_attributes(self):
        """Ensure the stakeholders widget has the appropriate attributes for Select2."""
        form = ProjectForm(user=self.user)
        attrs = form.fields['stakeholders'].widget.attrs
        self.assertIn('form-select', attrs.get('class', ''))
        self.assertIn('select2', attrs.get('class', ''))
        self.assertEqual(attrs.get('data-placeholder'), 'Search and select stakeholders...')

    def test_status_widget_attributes(self):
        """Ensure the status widget has the correct attributes."""
        form = ProjectForm(user=self.user)
        attrs = form.fields['status'].widget.attrs
        self.assertIn('form-select', attrs.get('class', ''))
        self.assertEqual(attrs.get('data-placeholder'), 'Choose status...')


class ProjectTaskFormTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="secret", email="test@example.com"
        )
        # Create two contacts for this user (simulate project stakeholders)
        self.contact1 = Contact.objects.create(
            user=self.user,
            contact_user=User.objects.create_user(username="contact1", password="secret")
        )
        self.contact2 = Contact.objects.create(
            user=self.user,
            contact_user=User.objects.create_user(username="contact2", password="secret")
        )
        # Create a project with these stakeholders
        self.project = Project.objects.create(
            name="Test Project",
            description="A sample project",
            is_public=True,
            start_date="2023-01-01",
            end_date="2023-12-31",
            status="In Progress",
            owner=self.user
        )
        self.project.stakeholders.set([self.contact1, self.contact2])

    def test_assigned_to_queryset(self):
        """ProjectTaskForm should restrict 'assigned_to' queryset to project's stakeholders."""
        form = ProjectTaskForm(project=self.project)
        qs = form.fields['assigned_to'].queryset
        self.assertIn(self.contact1, qs)
        self.assertIn(self.contact2, qs)
        # Optionally, ensure no extra contacts are present
        self.assertEqual(qs.count(), 2)

    def test_assigned_to_widget_attributes(self):
        """Ensure the 'assigned_to' widget uses Select2 with the proper attributes."""
        form = ProjectTaskForm(project=self.project)
        attrs = form.fields['assigned_to'].widget.attrs
        self.assertIn('form-select', attrs.get('class', ''))
        self.assertIn('select2', attrs.get('class', ''))
        self.assertEqual(attrs.get('data-placeholder'), 'Select assignees...')

    def test_other_fields_widget_attributes(self):
        """Test that other fields in ProjectTaskForm have the proper widget attributes."""
        form = ProjectTaskForm(project=self.project)
        # Title field
        title_attrs = form.fields['title'].widget.attrs
        self.assertIn('form-control', title_attrs.get('class', ''))
        # Description field
        desc_attrs = form.fields['description'].widget.attrs
        self.assertIn('form-control', desc_attrs.get('class', ''))
        self.assertEqual(desc_attrs.get('rows'), 3)
        # Due date field
        due_attrs = form.fields['due_date'].widget.attrs
        self.assertIn('form-control', due_attrs.get('class', ''))
        self.assertEqual(due_attrs.get('type'), 'date')
        # is_complete field
        is_complete_attrs = form.fields['is_complete'].widget.attrs
        self.assertIn('form-check-input', is_complete_attrs.get('class', ''))
