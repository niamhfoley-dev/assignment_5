from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from .models import CustomUser

User = get_user_model()


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')  # Redirect after a successful registration


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_object(self, queryset=None):
        # Return the currently logged in user as the profile object
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        # Return the currently logged in user as the profile object.
        return self.request.user

    def test_func(self):
        # Allow update only if the profile belongs to the current user.
        return self.get_object() == self.request.user
