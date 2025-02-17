# messages/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('sent/', views.SentMessagesView.as_view(), name='sent_messages'),
    path('send/', views.CreateMessageView.as_view(), name='send_message'),
    path('<int:pk>/reply/', views.ReplyMessageView.as_view(), name='reply_message'),
    path('<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('<int:pk>/archive/', views.ArchiveMessageView.as_view(), name='archive_message'),
]
