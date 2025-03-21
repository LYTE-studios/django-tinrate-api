import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models.user_models import User

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='John',
            last_name='Doe',
            username='johndoe',
            email='johndoe@example.com'
        )

    def test_user_creation(self):
        """Test that a user is correctly created."""
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.username, 'johndoe')
        self.assertEqual(self.user.email, 'johndoe@example.com')
        self.assertIsInstance(self.user.id, uuid.UUID)

    def test_username_uniqueness(self):
        """Test that the username field is unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                first_name='Jane',
                last_name='Doe',
                username='johndoe',
                email='janedoe@example.com'
            )

    def test_email_uniqueness(self):
        """Test that the email field is unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                first_name='Jane',
                last_name='Doe',
                username='janedoe',
                email='johndoe@example.com',
            )

    def test_str_method(self):
        """Test the string representation of the user model."""
        self.assertEqual(str(self.user), 'johndoe')