from django.db import models
from django.conf import settings
from django.utils import timezone
from contacts.models import Contact


class Project(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        # Add more statuses if needed

    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    stakeholders = models.ManyToManyField(Contact, blank=True, related_name='projects')
    is_public = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.IN_PROGRESS)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='projects',
        null=True
    )

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = [
            ('archive_project', 'Can archive a projects'),
        ]

    def __str__(self):
        return self.name

    @property
    def total_tasks(self):
        """Return total number of tasks for this project."""
        return self.tasks.count()

    @property
    def completed_tasks(self):
        """Number of tasks marked complete."""
        return self.tasks.filter(is_complete=True).count()

    @property
    def progress(self):
        """Calculate progress as ratio of completed tasks to total tasks."""
        total = self.total_tasks
        if total == 0:
            return 0
        return int((self.completed_tasks / total) * 100)


class ProjectJoinRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='join_requests')
    requesting_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.requesting_user} wants to join {self.project.name}"


class ProjectActivity(models.Model):
    """
    Logs any events / updates for the project:
    e.g. user joined, tasks updated, status changed, etc.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_created'
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.title} ({self.project.name})"


class ProjectTask(models.Model):
    """
    Individual tasks that belong to a project.
    'assigned_to' references project stakeholders (Contacts).
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_complete = models.BooleanField(default=False)
    assigned_to = models.ManyToManyField(Contact, blank=True, related_name="tasks")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.project.name}"
