from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def test_register_creates_user_and_redirects(self):
        url = reverse("register")
        resp = self.client.post(url, {
            "username": "brendan",
            "email": "brendan@example.com",
            "password1": "StrongPass12345!",
            "password2": "StrongPass12345!",
        })
        # Should redirect to dashboard after register
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username="brendan").exists())

    def test_login_works(self):
        User.objects.create_user(username="testuser", password="StrongPass12345!")
        url = reverse("login")
        resp = self.client.post(url, {
            "username": "testuser",
            "password": "StrongPass12345!",
        })
        self.assertEqual(resp.status_code, 302)  # redirect after login

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("dashboard"))
        # should redirect to login
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)
