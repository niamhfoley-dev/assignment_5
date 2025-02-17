from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsViewsTest(TestCase):
    def setUp(self):
        # Create a user for testing profile views and updates.
        self.user_password = 'testpass123'
        self.user = User.objects.create_user(
            username='testuser',
            password=self.user_password,
            email='test@example.com',
            first_name='Test',
            last_name='User',
            contact_number='123456'
        )

    def test_register_view_get(self):
        """Ensure the registration page loads."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_view_post_valid(self):
        """Posting valid data should create a user and redirect to login."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'contact_number': '78910',
            'password1': 'testpass321',
            'password2': 'testpass321',
        }
        response = self.client.post(reverse('register'), data)
        # Check that it redirects to the login page.
        self.assertRedirects(response, reverse('login'))
        # Verify that the user was created.
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'new@example.com')

    def test_profile_view_requires_login(self):
        """The profile view should require login."""
        response = self.client.get(reverse('profile'))
        login_url = reverse('login')
        self.assertRedirects(response, f"{login_url}?next={reverse('profile')}")

        # Now log in and try again.
        self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        # The view should pass the current user as 'user_profile'
        self.assertEqual(response.context['user_profile'], self.user)

    def test_profile_update_view_get(self):
        """The profile update view should load with current user's data."""
        self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(reverse('profile_update'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_update.html')
        form = response.context['form']
        # Check initial data
        self.assertEqual(form.initial.get('username'), self.user.username)
        self.assertEqual(form.initial.get('email'), self.user.email)
        self.assertEqual(form.initial.get('first_name'), self.user.first_name)
        self.assertEqual(form.initial.get('contact_number'), self.user.contact_number)

    def test_profile_update_view_post_valid(self):
        """Posting valid data should update the profile and redirect to profile view."""
        self.client.login(username=self.user.username, password=self.user_password)
        data = {
            'username': 'testuser',  # Keeping same username
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'contact_number': '99999',
        }
        response = self.client.post(reverse('profile_update'), data)
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.contact_number, '99999')
