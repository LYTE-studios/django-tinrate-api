from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterViewTest(APITestCase):

    """Test the user registration process and token generation."""

    def setUp(self):
        self.register_url = reverse("register_view")
        self.valid_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        self.invalid_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "differentpassword"
        }
    def test_register_user_success(self):
        """Test that a user can register successfully."""
        response = self.client.post(self.register_url, self.valid_payload, format="json")
        print(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(get_user_model().objects.count(), 1)
        