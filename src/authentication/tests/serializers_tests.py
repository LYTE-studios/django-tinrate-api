from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.test import APITestCase
from authentication.serializers.auth_serializers import RegisterSerializer

User = get_user_model()

class RegisterSerializerTest(APITestCase):
    def setUp(self):
        self.valid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        self.invalid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "differentpassword"
        }
        self.existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="password123"
        )
    def test_valid_serializer(self):
        """Test that a valid serializer passes validation and creates a user."""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, self.valid_data["username"])
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertTrue(user.check_password(self.valid_data["password"]))

    def test_password_mismatch(self):
        """Test that mismatched passwords raise a validation error."""
        serializer = RegisterSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"], ["Passwords do not match."])

    def test_duplicate_username(self):
        """Test that an existing username raises a validation error."""
        data = self.valid_data.copy()
        data["username"] = "existinguser"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertEqual(serializer.errors["username"], ["This username is already taken."])

    def test_duplicate_email(self):
        """Test that an existing email raises a validation error."""
        data = self.valid_data.copy()
        data["email"] = "existing@example.com"
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(serializer.errors["email"], ["This email is already registered."])

    