# messages/forms.py

from django import forms
from django.contrib.auth import get_user_model

from .models import Message
from contacts.models import Contact  # or from django.contrib.auth.models import User

User = get_user_model()


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # We'll pass the current user from the view
        super().__init__(*args, **kwargs)

        # If you want to limit recipients to the user's contacts:
        if user is not None:
            self.fields['recipient'].queryset = User.objects.filter(
                pk__in=Contact.objects.filter(user=user).values_list('contact_user__pk', flat=True)
            )
            # If you want to reference a user field, adjust accordingly:
            # self.fields['recipient'].queryset = User.objects.all().exclude(pk=user.pk)

        # Optional: add a nice class or placeholder for styling (especially if using Select2)
        self.fields['recipient'].widget.attrs.update({
            'class': 'form-select select2',
            'data-placeholder': 'Search or select a contact...'
        })

        self.fields['subject'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter subject...'
        })

        self.fields['body'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Type your message here...',
            'rows': '5'
        })


class ReplyMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Type your reply here...',
                'rows': '5'
            }),
        }
