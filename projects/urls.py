from django.urls import path
from . import views
from .views import RequestJoinProjectView, AcceptJoinRequestView, RejectJoinRequestView, LeaveProjectView, TaskCreateView, TaskUpdateView

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    # Join Requests
    path('<int:pk>/join/', RequestJoinProjectView.as_view(), name='request_join_project'),
    path('join-request/<int:jr_pk>/accept/', AcceptJoinRequestView.as_view(), name='accept_join_request'),
    path('join-request/<int:jr_pk>/reject/', RejectJoinRequestView.as_view(), name='reject_join_request'),
    path('<int:pk>/leave/', LeaveProjectView.as_view(), name='leave_project'),

    # Task management
    path('<int:project_pk>/tasks/create/', TaskCreateView.as_view(), name='tasks_create'),
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='tasks_edit'),
]
