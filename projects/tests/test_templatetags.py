from django.test import TestCase
from django.template import Template, Context
from django.contrib.auth import get_user_model
from projects.models import Project
from contacts.models import Contact

User = get_user_model()


class InStakeholdersFilterTest(TestCase):
    def setUp(self):
        # Create two users: one will be the project owner, one will be a stakeholder.
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.stakeholder_user = User.objects.create_user(username="stakeholder", password="secret")
        self.other_user = User.objects.create_user(username="other", password="secret")

        # Create a project with the owner.
        self.project = Project.objects.create(
            name="Test Project",
            owner=self.owner,
            # Add other required fields as needed.
        )

        # Create a Contact for the owner referencing the stakeholder user.
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
