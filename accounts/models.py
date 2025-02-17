from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    # You can define custom model-level permissions if needed
    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = [
            # e.g., ('can_manage_profiles', 'Can manage user profiles'),
        ]

    def __str__(self):
        return self.username
