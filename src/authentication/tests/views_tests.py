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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(get_user_model().objects.count(), 1)
    
    def test_register_user_passwords_not_matching(self):
        """Test that passwords do not match."""
        response = self.client.post(self.register_url, self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"password": ["Passwords do not match."]})

    def test_register_user_missing_username(self):
        """Test that registration fails when username is missing."""
        invalid_payload = self.invalid_payload.copy()
        del invalid_payload["username"]
        response = self.client.post(self.register_url, self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_missing_email(self):
        """That registration fails when email is missing."""
        invalid_payload = self.invalid_payload.copy()
        del invalid_payload["email"]
        response = self.client.post(self.register_url, self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_missing_confirm_password(self):
        """That registration fails when confirm_password is missing."""
        invalid_payload = self.invalid_payload.copy()
        del invalid_payload["confirm_password"]
        response = self.client.post(self.register_url, self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_existing_email(self):
        """Test that registration fails when the email already exists."""
        get_user_model().objects.create_user(
            username="newuser", email="newuser@example.com", password="password123"
        )
        response = self.client.post(self.register_url, self.valid_payload, format="json")
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
