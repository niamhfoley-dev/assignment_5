from datetime import date

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectJoinRequest, ProjectActivity, ProjectTask
from contacts.models import Contact
from messaging.models import Message

User = get_user_model()


class ProjectsViewsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create users
        self.owner = User.objects.create_user(username='owner', password='secret')
        self.other = User.objects.create_user(username='other', password='secret')
        self.third = User.objects.create_user(username='third', password='secret')
        # Create a Contact so that owner has other in contacts (simulate stakeholder relationship)
        self.contact = Contact.objects.create(
            user=self.owner,
            contact_user=self.other,
            phone='1234567890',
            note='Test contact'
        )
        # Create a public project owned by self.owner and add the contact

        self.project = Project.objects.create(
            name="Test Project",
            description="A sample project for testing.",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            is_public=True,
            status=Project.Status.IN_PROGRESS,
            owner=self.owner
        )

        self.project.stakeholders.add(self.contact)
        # Create a sample task for the project
        self.task = ProjectTask.objects.create(
            project=self.project,
            title="Initial Task",
            description="Task description",
            due_date=date(2023, 12, 31),
            is_complete=False,
        )
        # Create a sample join request from self.third (not in contacts)
        self.join_request = ProjectJoinRequest.objects.create(
            project=self.project,
            requesting_user=self.third,
            status=ProjectJoinRequest.RequestStatus.PENDING
        )
        # Log in as owner by default for some tests; individual tests can log in as needed.
        self.client.login(username='owner', password='secret')

    def test_project_create_view_post(self):
        """Test that posting valid data to ProjectCreateView creates a project."""
        url = reverse('project_create')
        data = {
            'name': 'New Project',
            'description': 'New project description',
            'is_public': True,
            'start_date': date(2023, 1, 1),
            'end_date': date(2023, 12, 31),
            'status': Project.Status.IN_PROGRESS,
            # For stakeholders, send the contact id; our ProjectForm filters to owner's contacts.
            'stakeholders': [str(self.contact.pk)],
        }
        # Log in as owner and post data.
        self.client.login(username='owner', password='secret')
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('project_list'))
        new_project = Project.objects.get(name='New Project')
        self.assertEqual(new_project.owner, self.owner)
        # Log an activity, etc.
        self.assertTrue(ProjectActivity.objects.filter(project=new_project, title="Project Created").exists())

    def test_project_update_view(self):
        """Test that updating a project via ProjectUpdateView works."""
        url = reverse('project_update', args=[self.project.pk])
        data = {
            'name': 'Updated Project Name',
            'description': self.project.description,
            'is_public': self.project.is_public,
            'start_date': self.project.start_date,
            'end_date': self.project.end_date,
            'status': self.project.status,
            'stakeholders': [str(self.contact.pk)],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('project_list'))
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')
        self.assertTrue(ProjectActivity.objects.filter(project=self.project, title="Project Updated").exists())

    def test_project_list_view(self):
        """Test that the project list view returns only projects for the owner when view=mine."""
        url = reverse('project_list') + '?view=mine'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Owner should see the project they own.
        projects = response.context['projects']
        self.assertIn(self.project, projects)

    def test_project_detail_view(self):
        """Test that the detail view shows a project if public or user is stakeholder/owner."""
        url = reverse('project_detail', args=[self.project.pk])
        # Test as owner
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        # Test as stakeholder: log in as other.
        self.client.logout()
        self.client.login(username='other', password='secret')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_project_delete_view(self):
        """Test that a project can be deleted if confirmation name matches."""
        url = reverse('project_delete', args=[self.project.pk])
        data = {'confirmName': self.project.name}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('project_list'))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(ProjectActivity.objects.filter(title="Project Deleted").exists())

    def test_request_join_project_view(self):
        """Test that a join request is created (or updated) for a public project."""
        self.client.logout()
        self.client.login(username='third', password='secret')
        url = reverse('request_join_project', args=[self.project.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        # Since self.third already has a join request from setUp, the status should remain PENDING.
        join_req = ProjectJoinRequest.objects.get(pk=self.join_request.pk)
        self.assertEqual(join_req.status, ProjectJoinRequest.RequestStatus.PENDING)

    def test_accept_join_request_view(self):
        """Test that the owner can accept a join request, adding the requesting user to stakeholders."""
        url = reverse('accept_join_request', args=[self.join_request.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        join_req = ProjectJoinRequest.objects.get(pk=self.join_request.pk)
        self.assertEqual(join_req.status, ProjectJoinRequest.RequestStatus.ACCEPTED)
        # Check that the stakeholder added is the contact of the owner representing the requesting user.
        # According to our view, we add contact_of_owner.
        from contacts.models import Contact
        contact_of_owner = Contact.objects.get(user=self.owner, contact_user=self.third)
        self.assertIn(contact_of_owner, self.project.stakeholders.all())
        self.assertTrue(ProjectActivity.objects.filter(title="Join Request Accepted").exists())

    def test_reject_join_request_view(self):
        """Test that the owner can reject a join request and a message is sent to the requesting user."""
        url = reverse('reject_join_request', args=[self.join_request.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        join_req = ProjectJoinRequest.objects.get(pk=self.join_request.pk)
        self.assertEqual(join_req.status, ProjectJoinRequest.RequestStatus.REJECTED)
        # Check that a message was sent to the requesting user.
        self.assertTrue(Message.objects.filter(recipient=self.join_request.requesting_user,
                                               subject__icontains="Rejected").exists())
        self.assertTrue(ProjectActivity.objects.filter(title="Join Request Rejected").exists())

    def test_leave_project_view(self):
        """Test that a stakeholder can leave a project and the owner is notified."""
        # Log in as the stakeholder (other) since owner cannot leave.
        self.client.logout()
        self.client.login(username='other', password='secret')
        url = reverse('leave_project', args=[self.project.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        # Check that the contact representing the stakeholder has been removed.
        from contacts.models import Contact
        try:
            Contact.objects.get(user=self.owner, contact_user=self.other)
            self.fail("Contact should have been removed from project stakeholders.")
        except Contact.DoesNotExist:
            pass
        # Check that a notification message was sent.
        self.assertTrue(Message.objects.filter(recipient=self.owner,
                                               subject__icontains="Stakeholder Left").exists())
        self.assertTrue(ProjectActivity.objects.filter(title="Stakeholder Left").exists())

    def test_task_create_view(self):
        """Test that a task can be created for a project."""
        # Log in as owner (or stakeholder with management permissions)
        self.client.login(username='owner', password='secret')
        url = reverse('task_create', args=[self.project.pk])
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'due_date': date(2023, 12, 31),
            'is_complete': False,
            # 'assigned_to' should be a list of contact ids; we'll assign the existing contact.
            'assigned_to': [str(self.contact.pk)],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        self.assertTrue(ProjectTask.objects.filter(title="New Task", project=self.project).exists())
        self.assertTrue(ProjectActivity.objects.filter(title__icontains="Task Created").exists())

    def test_task_update_view(self):
        """Test that updating a task works correctly."""
        # Create a task first
        task = ProjectTask.objects.create(
            project=self.project,
            title="Task Update Test",
            description="Original description",
            due_date=date(2023, 12, 31),
            is_complete=False,
        )
        url = reverse('task_update', args=[task.pk])
        data = {
            'title': 'Task Updated',
            'description': 'Updated description',
            'due_date': date(2023, 12, 31),
            'is_complete': True,
            'assigned_to': [str(self.contact.pk)],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]))
        task.refresh_from_db()
        self.assertEqual(task.title, 'Task Updated')
        self.assertTrue(task.is_complete())
        self.assertTrue(ProjectActivity.objects.filter(title__icontains="Task Completed").exists() or
                        ProjectActivity.objects.filter(title__icontains="Task Updated").exists())

    def test_can_manage_project(self):
        """Test the can_manage_project logic used in task views."""
        # As owner, can manage project.
        self.assertTrue(self.project.owner == self.owner)
        # For a stakeholder, use a contact with contact_user equal to the project owner.
        self.client.logout()
        self.client.login(username='other', password='secret')
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        # This is a basic test to ensure that the stakeholder view loads.
        self.assertEqual(response.status_code, 200)
