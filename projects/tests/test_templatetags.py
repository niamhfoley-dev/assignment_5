from django.test import TestCase
from django.template import Template, Context
from django.contrib.auth import get_user_model
from projects.models import Project
from contacts.models import Contact

User = get_user_model()


class InStakeholdersFilterTest(TestCase):
    def setUp(self):
        # Create three users:
        # - self.owner: The project owner.
        # - self.stakeholder_user: A user who will be added as a stakeholder.
        # - self.other_user: An extra user for testing purposes.
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.stakeholder_user = User.objects.create_user(username="stakeholder", password="secret")
        self.other_user = User.objects.create_user(username="other", password="secret")

        # Create a project owned by self.owner.
        # Note: Be sure to provide any required fields (like start_date and end_date)
        # if they're mandatory in your Project model.
        self.project = Project.objects.create(
            name="Test Project",
            owner=self.owner,
            start_date="2023-01-01",  # example values if required
            end_date="2023-12-31",  # example values if required
            description="A project for testing purposes.",
            status=Project.Status.IN_PROGRESS,
            is_public=True,
        )

        # Create a Contact that represents the stakeholder relationship.
        # This contact is created for the owner, referencing the stakeholder_user.
        self.contact = Contact.objects.create(
            user=self.owner,
            contact_user=self.stakeholder_user,
            phone="1234567890",
            note="Test note"
        )

        # Add this contact to the project's stakeholders.
        self.project.stakeholders.add(self.contact)

    def render_template(self, template_string, context):
        template = Template(template_string)
        return template.render(Context(context)).strip()

    def test_in_stakeholders_filter_returns_true(self):
        """The filter should return True when the user is a stakeholder."""
        template_str = "{% load projects_extras %}{{ user|in_stakeholders:project }}"
        context = {"user": self.stakeholder_user, "project": self.project}
        rendered = self.render_template(template_str, context)
        self.assertEqual(rendered, "True")

    def test_in_stakeholders_filter_returns_false(self):
        """The filter should return False when the user is not a stakeholder."""
        template_str = "{% load projects_extras %}{{ user|in_stakeholders:project }}"
        context = {"user": self.other_user, "project": self.project}
        rendered = self.render_template(template_str, context)
        self.assertEqual(rendered, "False")
