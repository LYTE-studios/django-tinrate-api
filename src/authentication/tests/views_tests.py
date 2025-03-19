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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.user_data = {
            "email": "newuser@example.com",
            "username": "newuser@example.com",
            "password": "password123"
        }
        self.user = get_user_model().objects.create_user(
            email="newuser@example.com",
            username="newuser@example.com",
            password="password123",
        )
        self.login_url = reverse('login_view')

    def test_valid_login(self):
        """Test that a valid email and password pair returns a user."""
        data = {
            "email":self.user.email,
            "password": self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"], self.user.id)

    def test_login_invalid_password(self):
        """Test login with an incorrect password."""
        response = self.client.post(self.login_url, {
            "email": "newuser@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["Invalid credentials. Please try again."]})

    def test_login_unregistered_email(self):
        """Test login with an email that does not exist."""
        response = self.client.post(self.login_url, {
             "email": "doesnotexist@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"email": ["This email is not registered."]} )

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = self.client.post(self.login_url, {"email": "newuser@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_blank_fields(self):
        """Test login with blank email and password."""
        response = self.client.post(self.login_url, { "email": "", "password": "",})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)