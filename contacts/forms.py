from django import forms
from django.contrib.auth import get_user_model
from .models import Contact

User = get_user_model()


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['contact_user', 'phone', 'note']

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Restrict available users to add as a contact (exclude self)
        if self.request_user:
            self.fields['contact_user'].queryset = User.objects.exclude(pk=self.request_user.pk)

        # Adjust widget for a nicer multi-search (e.g., using Select2 or standard select)
        self.fields['contact_user'].widget.attrs.update({
            'class': 'form-select',
        })

        # Add nice form classes to phone and note fields
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter phone number',
        })
        self.fields['note'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes (optional)',
        })
