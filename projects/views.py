from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from contacts.models import Contact
from messaging.models import Message
from .models import (
    Project, ProjectJoinRequest, ProjectActivity, ProjectTask
)
from .forms import ProjectForm, ProjectTaskForm


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')

    def get_form_kwargs(self):
        """ Pass the current user to the form. """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """ Attach owner, create project, then log activity. """
        form.instance.owner = self.request.user
        response = super().form_valid(form)  # Saves the project
        project = self.object

        # Create activity record
        ProjectActivity.objects.create(
            project=project,
            title="Project Created",
            description=f"{self.request.user.username} created this project.",
            created_by=self.request.user
        )
        return response


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')
    context_object_name = 'project'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """ On successful update, log activity. """
        response = super().form_valid(form)
        project = self.object
        ProjectActivity.objects.create(
            project=project,
            title="Project Updated",
            description=f"{self.request.user.username} updated this project.",
            created_by=self.request.user
        )
        return response


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        view_filter = self.request.GET.get('view', 'mine')
        query = self.request.GET.get('q', '')
        status_filter = self.request.GET.get('status', '')

        if query:
            queryset = queryset.filter(name__icontains=query)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if view_filter == 'mine':
            queryset = queryset.filter(owner=self.request.user)
        elif view_filter == 'public':
            queryset = queryset.filter(is_public=True)

        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['status'] = self.request.GET.get('status', '')
        context['view'] = self.request.GET.get('view', 'mine')
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        """ Ensure user only sees project if it's public or they own/belong to it. """
        qs = super().get_queryset()
        return qs.filter(
            Q(is_public=True) | Q(owner=self.request.user) |
            Q(stakeholders__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        # Tasks & Activity
        context['task_list'] = project.tasks.all().order_by('due_date')
        context['activity_list'] = project.activities.all()
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')
    permission_required = 'projects.delete_project'
    context_object_name = 'project'

    def get_queryset(self):
        # Limit deletion to projects owned by the logged-in user.
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        confirm_name = request.POST.get('confirmName', '')
        if confirm_name == self.object.name:
            # Log activity before the project is deleted.
            ProjectActivity.objects.create(
                project=self.object,
                title="Project Deleted",
                description=f"{request.user.username} deleted this project.",
                created_by=request.user
            )
            messages.success(request, "Project successfully deleted.")
            return super().post(request, *args, **kwargs)
        else:
            messages.error(request, "Deletion canceled: typed name does not match the project.")
            return redirect('project_detail', pk=self.object.pk)


class RequestJoinProjectView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, is_public=True)

        if project.owner == request.user:
            messages.error(request, "You own this project.")
            return redirect('project_detail', pk=project.pk)

        is_stakeholder = project.stakeholders.filter(user=request.user).exists()
        if is_stakeholder:
            messages.info(request, "You are already a stakeholder in this project.")
            return redirect('project_detail', pk=project.pk)

        join_request, created = ProjectJoinRequest.objects.get_or_create(
            project=project,
            requesting_user=request.user,
            defaults={'status': ProjectJoinRequest.RequestStatus.PENDING}
        )
        if not created:
            # Already had a request
            if join_request.status == ProjectJoinRequest.RequestStatus.PENDING:
                messages.info(request, "A join request is already pending.")
            else:
                messages.info(request, f"You previously had a {join_request.status} request.")
        else:
            # Notify the project owner
            subject = f"Join Request for {project.name}"
            body = (
                f"{request.user.username} has requested to join your project '{project.name}'.\n"
                f"View project: {request.build_absolute_uri(reverse_lazy('project_detail', args=[project.pk]))}"
            )
            Message.objects.create(
                sender=request.user,
                recipient=project.owner,
                subject=subject,
                body=body
            )

            # Log activity
            ProjectActivity.objects.create(
                project=project,
                title="Join Request Submitted",
                description=f"{request.user.username} requested to join this project.",
                created_by=request.user
            )

            messages.success(request, "Join request sent! The project owner will be notified.")
        return redirect('project_detail', pk=project.pk)


class AcceptJoinRequestView(LoginRequiredMixin, View):
    def post(self, request, jr_pk, *args, **kwargs):
        join_request = get_object_or_404(ProjectJoinRequest, pk=jr_pk)
        project = join_request.project

        if project.owner != request.user:
            messages.error(request, "You are not the project owner.")
            return redirect('project_detail', pk=project.pk)

        # Mark as accepted
        join_request.status = ProjectJoinRequest.RequestStatus.ACCEPTED
        join_request.save()

        # Add user to stakeholders
        contact_of_requesting_user, _ = Contact.objects.get_or_create(
            user=join_request.requesting_user,
            contact_user=request.user
        )
        contact_of_owner, _ = Contact.objects.get_or_create(
            user=request.user,
            contact_user=join_request.requesting_user
        )
        project.stakeholders.add(contact_of_owner)

        # Log activity
        ProjectActivity.objects.create(
            project=project,
            title="Join Request Accepted",
            description=f"{join_request.requesting_user.username} was added to project stakeholders.",
            created_by=request.user
        )

        messages.success(request, f"You accepted {join_request.requesting_user.username} to the project.")
        return redirect('project_detail', pk=project.pk)


class RejectJoinRequestView(LoginRequiredMixin, View):
    def post(self, request, jr_pk, *args, **kwargs):
        join_request = get_object_or_404(ProjectJoinRequest, pk=jr_pk)
        project = join_request.project

        if project.owner != request.user:
            messages.error(request, "You are not the project owner.")
            return redirect('project_detail', pk=project.pk)

        join_request.status = ProjectJoinRequest.RequestStatus.REJECTED
        join_request.save()

        subject = f"Join Request for {project.name} Rejected"
        body = (
            f"Hello {join_request.requesting_user.username},\n\n"
            f"Your request to join the project '{project.name}' has been rejected by the project owner.\n\n"
            "Please contact the project owner if you have any questions."
        )
        Message.objects.create(
            sender=request.user,
            recipient=join_request.requesting_user,
            subject=subject,
            body=body
        )

        # Log activity
        ProjectActivity.objects.create(
            project=project,
            title="Join Request Rejected",
            description=f"{join_request.requesting_user.username}'s join request was rejected.",
            created_by=request.user
        )

        messages.info(request, f"You rejected {join_request.requesting_user.username}. A notification has been sent to them.")
        return redirect('project_detail', pk=project.pk)


class LeaveProjectView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)

        if project.owner == request.user:
            messages.error(request, "Project owners cannot leave their own project.")
            return redirect('project_detail', pk=project.pk)

        try:
            contact = project.stakeholders.get(user=project.owner, contact_user=request.user)
        except Contact.DoesNotExist:
            messages.info(request, "You are not a stakeholder in this project.")
            return redirect('project_detail', pk=project.pk)

        project.stakeholders.remove(contact)

        # Notify the owner
        subject = f"Stakeholder Left: {request.user.username}"
        body = (
            f"Hello {project.owner.username},\n\n"
            f"This is to inform you that {request.user.username} has left your project '{project.name}'.\n\n"
            "Regards,\nYour Project Management System"
        )
        Message.objects.create(
            sender=request.user,
            recipient=project.owner,
            subject=subject,
            body=body
        )

        # Log activity
        ProjectActivity.objects.create(
            project=project,
            title="Stakeholder Left",
            description=f"{request.user.username} left the project.",
            created_by=request.user
        )

        messages.success(request, "You have left the project. The project owner has been notified.")
        return redirect('project_detail', pk=project.pk)


"""
Task Creation & Update
"""


class TaskCreateView(LoginRequiredMixin, View):
    """Form to create a new task for a specific project."""

    def get(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk)
        if not self.can_manage_project(request.user, project):
            messages.error(request, "You do not have permission to add tasks to this project.")
            return redirect('project_detail', pk=project.pk)

        form = ProjectTaskForm(project=project)
        return render(request, 'projects/tasks/task_form.html', {'form': form, 'project': project})

    def post(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk)
        if not self.can_manage_project(request.user, project):
            messages.error(request, "You do not have permission to add tasks to this project.")
            return redirect('project_detail', pk=project.pk)

        form = ProjectTaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()

            # Log activity for new task
            ProjectActivity.objects.create(
                project=project,
                title=f"Task Created: {task.title}",
                description=f"Assigned to: {', '.join([c.contact_user.username for c in task.assigned_to.all()])}",
                created_by=request.user
            )

            messages.success(request, "Task created successfully.")
            return redirect('project_detail', pk=project.pk)
        return render(request, 'projects/tasks/task_form.html', {'form': form, 'project': project})

    def can_manage_project(self, user, project):
        if project.owner == user:
            return True
        return project.stakeholders.filter(contact_user=user).exists()


class TaskUpdateView(LoginRequiredMixin, View):
    """Edit an existing task."""

    def get(self, request, pk):
        task = get_object_or_404(ProjectTask, pk=pk)
        project = task.project
        if not self.can_manage_project(request.user, project):
            messages.error(request, "You do not have permission to edit tasks for this project.")
            return redirect('project_detail', pk=project.pk)

        form = ProjectTaskForm(instance=task, project=project)
        return render(request, 'projects/tasks/task_form.html', {'form': form, 'project': project, 'task': task})

    def post(self, request, pk):
        task = get_object_or_404(ProjectTask, pk=pk)
        project = task.project
        if not self.can_manage_project(request.user, project):
            messages.error(request, "You do not have permission to edit tasks for this project.")
            return redirect('project_detail', pk=project.pk)

        form = ProjectTaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            old_status = task.is_complete
            updated_task = form.save()

            # Log status changes or updates
            if old_status != updated_task.is_complete:
                status_text = "completed" if updated_task.is_complete else "reopened"
                ProjectActivity.objects.create(
                    project=project,
                    title=f"Task {status_text}: {updated_task.title}",
                    description=f"Task was marked {status_text} by {request.user.username}.",
                    created_by=request.user
                )
            else:
                ProjectActivity.objects.create(
                    project=project,
                    title=f"Task Updated: {updated_task.title}",
                    description=f"Edited by {request.user.username}.",
                    created_by=request.user
                )

            messages.success(request, "Task updated successfully.")
            return redirect('project_detail', pk=project.pk)
        return render(request, 'projects/tasks/task_form.html', {'form': form, 'project': project, 'task': task})

    def can_manage_project(self, user, project):
        if project.owner == user:
            return True
        return project.stakeholders.filter(contact_user=user).exists()
