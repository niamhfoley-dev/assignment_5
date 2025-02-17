# messaging/context_processors.py

from .models import Message


def unread_messages_count(request):
    """
    Return a dictionary with unread messages count for the authenticated user.
    If user is anonymous, return 0.
    """
    if request.user.is_authenticated:
        return {
            'unread_messages_count': Message.objects.filter(
                recipient=request.user,
                # Suppose you track read status with a boolean 'is_read'
                # If you only have 'is_archived', adjust logic accordingly.
                is_archived=False,
                is_read=False,
            ).count()
        }
    return {'unread_messages_count': 0}
