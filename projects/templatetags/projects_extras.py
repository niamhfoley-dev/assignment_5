# projects/templatetags/projects_extras.py

from django import template

register = template.Library()


@register.filter
def in_stakeholders(user, project):
    """Return True if user is in the project's stakeholder list."""
    return user in [c.contact_user for c in project.stakeholders.all()]
