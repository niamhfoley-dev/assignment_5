from django.contrib import admin
from .models import Project, ProjectJoinRequest

admin.site.register(Project)
admin.site.register(ProjectJoinRequest)