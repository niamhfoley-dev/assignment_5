from django.test import TestCase
from django.urls import reverse


class HomeViewTest(TestCase):
    def test_home_view_status_and_template(self):
        # Assumes your home view is named 'home' in your URL configuration.
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home.html')
