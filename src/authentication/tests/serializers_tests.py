from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.test import APITestCase
from authentication.serializers.auth_serializers import RegisterSerializer, LoginSerializer

User = get_user_model()

class RegisterSerializerTest(APITestCase):
    def setUp(self):
        self.valid_data = {
            "username": "newuser@example.com",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        self.invalid_data = {
            "username": "newuser@example.com",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "differentpassword"
        }
        self.existing_user = User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="password123"
        )
    def test_valid_serializer(self):
        """Test that a valid serializer passes validation and creates a user."""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, self.valid_data["email"])
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertTrue(user.check_password(self.valid_data["password"]))

    def test_password_mismatch(self):
        """Test that mismatched passwords raise a validation error."""
        serializer = RegisterSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"], ["Passwords do not match."])


    def test_duplicate_email(self):
        """Test that an existing email raises a validation error."""
        data = self.valid_data.copy()
        data["email"] = "existing@example.com"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(serializer.errors["email"], ["This email is already registered."])


class LoginSerializerTest(APITestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="password123",
        )
        self.valid_data = {
            "email": "existing@example.com",
            "password": "password123",
        }
        self.invalid_email_data = {
            "email": "nonexisting@example.com",
            "password": "password123",
        }
        self.invalid_password_data = {
            "email": "existing@example.com",
            "password": "wrongpassword",
        }
    def test_valid_login(self):
        """Test that a valid email and passowrd pair returns a user."""
        serializer = LoginSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.validated_data["user"]
        self.assertEqual(user.email, self.valid_data["email"])

    def test_email_not_registered(self):
        """Test that an unregistered email raises a validation error."""
        serializer = LoginSerializer(data=self.invalid_email_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(serializer.errors["email"], ["This email is not registered."])

    def test_invalid_password(self):
        """Test that an incorrect password raises a validation error."""
        serializer = LoginSerializer(data=self.invalid_password_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"], ["Invalid credentials. Please try again."])

    