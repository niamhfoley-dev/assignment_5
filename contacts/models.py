# contacts/models.py

from django.db import models
from django.conf import settings


class Contact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    # The user that this contact references
    contact_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_of',
        help_text="Select an existing user in the system",
        null=True,
    )

    # Optional extra fields
    phone = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view')

    def __str__(self):
        # e.g., show the contact_user's full_name or username
        return self.contact_user.get_full_name() or self.contact_user.username
