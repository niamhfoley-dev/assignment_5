from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import (
    CustomUserCreationForm,
    CustomUserUpdateForm,
    CustomLoginForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)

User = get_user_model()


class CustomUserFormsTest(TestCase):
    def test_custom_user_creation_form_valid(self):
        """Test that the user creation form is valid with matching passwords."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'contact_number': '12345',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_custom_user_creation_form_invalid(self):
        """Test that mismatched passwords cause a validation error."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'contact_number': '12345',
            'password1': 'strongpassword123',
            'password2': 'differentpassword',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_custom_user_update_form(self):
        """Test that the update form prepopulates and updates the user."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="secret123",
            first_name="Test",
            last_name="User",
            contact_number="11111",
        )
        form_data = {
            'username': 'testuser_updated',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'contact_number': '98765',
        }
        form = CustomUserUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid(), form.errors)
        updated_user = form.save()
        self.assertEqual(updated_user.username, 'testuser_updated')
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.contact_number, '98765')

    def test_custom_login_form_widget_attrs(self):
        """Test that the login form's username and password fields have proper Bootstrap classes."""
        form = CustomLoginForm()
        self.assertIn('form-control', form.fields['username'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['password'].widget.attrs.get('class', ''))

    def test_custom_password_reset_form_widget_attrs(self):
        """Test that the password reset form's email field has proper Bootstrap classes."""
        form = CustomPasswordResetForm()
        self.assertIn('form-control', form.fields['email'].widget.attrs.get('class', ''))

    def test_custom_set_password_form_valid(self):
        """Test that the set password form validates correctly and uses the proper widget classes."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="secret123",
        )
        form_data = {
            'new_password1': 'newstrongpassword123',
            'new_password2': 'newstrongpassword123',
        }
        form = CustomSetPasswordForm(user, data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('form-control', form.fields['new_password1'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['new_password2'].widget.attrs.get('class', ''))
