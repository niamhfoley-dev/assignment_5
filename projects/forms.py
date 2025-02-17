# projects/forms.py

from django import forms
from .models import Project, ProjectTask
from contacts.models import Contact


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'is_public',
            'start_date',
            'end_date',
            'status',
            'stakeholders',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Project Name',
            'description': 'Project Description',
            'is_public': 'Project Is Public',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'stakeholders': 'Stakeholders',
            'status': 'Project Status',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Restrict stakeholders to the user’s own contacts
        if user is not None:
            self.fields['stakeholders'].queryset = Contact.objects.filter(user=user)

        # Instead of replacing the widget, update its attributes:
        self.fields['stakeholders'].widget.attrs.update({
            'class': 'form-select select2',
            'data-placeholder': 'Search and select stakeholders...',
        })

        # Optionally update other widget attributes if needed.
        self.fields['status'].widget.attrs.update({
            'class': 'form-select',
            'data-placeholder': 'Choose status...'
        })


class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['title', 'description', 'due_date', 'is_complete', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2',
                    'data-placeholder': 'Select assignees...'
                }
            ),
            'is_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            # Restrict the 'assigned_to' field to only the project's stakeholders.
            self.fields['assigned_to'].queryset = project.stakeholders.all()
