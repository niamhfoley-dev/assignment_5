from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectJoinRequest, ProjectActivity, ProjectTask
from contacts.models import Contact

User = get_user_model()


class ProjectModelTest(TestCase):
    def setUp(self):
        # Create an owner and another user to be a contact/stakeholder.
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.other = User.objects.create_user(username="other", password="secret")
        # Create a contact for the owner referencing the other user.
        self.contact = Contact.objects.create(
            user=self.owner,
            contact_user=self.other,
            phone="1234567890",
            note="Test contact"
        )
        # Create a project with the owner, add the contact as a stakeholder.
        self.project = Project.objects.create(
            name="Test Project",
            description="A sample project for testing.",
            start_date="2023-01-01",
            end_date="2023-12-31",
            is_public=True,
            status=Project.Status.IN_PROGRESS,
            owner=self.owner
        )
        self.project.stakeholders.add(self.contact)

    def test_project_str(self):
        """Test that the __str__ method returns the project name."""
        self.assertEqual(str(self.project), "Test Project")

    def test_total_and_completed_tasks_and_progress(self):
        """Test the task counts and progress calculation."""
        # Initially, there are no tasks.
        self.assertEqual(self.project.total_tasks, 0)
        self.assertEqual(self.project.completed_tasks, 0)
        self.assertEqual(self.project.progress, 0)

        # Create two tasks: one incomplete, one complete.
        task1 = ProjectTask.objects.create(
            project=self.project,
            title="Task 1",
            description="First task",
            due_date="2023-06-01",
            is_complete=False
        )
        task2 = ProjectTask.objects.create(
            project=self.project,
            title="Task 2",
            description="Second task",
            due_date="2023-06-15",
            is_complete=True
        )
        self.assertEqual(self.project.total_tasks, 2)
        self.assertEqual(self.project.completed_tasks, 1)
        self.assertEqual(self.project.progress, 50)


class ProjectJoinRequestTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.requesting = User.objects.create_user(username="requesting", password="secret")
        self.project = Project.objects.create(
            name="Join Request Project",
            description="Testing join requests.",
            start_date="2023-01-01",
            end_date="2023-12-31",
            is_public=True,
            status=Project.Status.IN_PROGRESS,
            owner=self.owner
        )

    def test_join_request_str_and_status(self):
        """Test that a join request is created correctly."""
        join_request = ProjectJoinRequest.objects.create(
            project=self.project,
            requesting_user=self.requesting,
            status=ProjectJoinRequest.RequestStatus.PENDING
        )
        expected_str = f"{self.requesting} wants to join {self.project.name}"
        self.assertEqual(str(join_request), expected_str)
        self.assertEqual(join_request.status, ProjectJoinRequest.RequestStatus.PENDING)


class ProjectActivityTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.project = Project.objects.create(
            name="Activity Project",
            description="Project activity testing.",
            start_date="2023-01-01",
            end_date="2023-12-31",
            is_public=True,
            status=Project.Status.IN_PROGRESS,
            owner=self.owner
        )

    def test_activity_str(self):
        """Test that ProjectActivity __str__ returns the expected string."""
        activity = ProjectActivity.objects.create(
            project=self.project,
            title="Project Updated",
            description="Updated project details.",
            created_by=self.owner
        )
        expected_str = f"{activity.title} ({self.project.name})"
        self.assertEqual(str(activity), expected_str)


class ProjectTaskTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="secret")
        self.project = Project.objects.create(
            name="Task Project",
            description="Testing tasks in a project.",
            start_date="2023-01-01",
            end_date="2023-12-31",
            is_public=True,
            status=Project.Status.IN_PROGRESS,
            owner=self.owner
        )

    def test_task_str(self):
        """Test that the __str__ method of ProjectTask returns the expected string."""
        task = ProjectTask.objects.create(
            project=self.project,
            title="Task Example",
            description="An example task.",
            due_date="2023-06-01",
            is_complete=False
        )
        expected_str = f"{task.title} - {self.project.name}"
        self.assertEqual(str(task), expected_str)
