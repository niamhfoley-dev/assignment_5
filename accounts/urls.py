from django.urls import path

from .forms import CustomLoginForm, CustomPasswordResetForm, CustomSetPasswordForm
from .views import RegisterView, ProfileUpdateView, ProfileView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=CustomLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_update'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/reset/password_reset_form.html',
        form_class=CustomPasswordResetForm
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/reset/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/reset/password_reset_confirm.html',
        form_class=CustomSetPasswordForm,
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/reset/password_reset_complete.html'),
         name='password_reset_complete'),
]
