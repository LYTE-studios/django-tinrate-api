from django.test import TestCase
from rest_framework.exceptions import ValidationError
from users import serializers
from users.serializers.user_serializer import UserSerializer
from users.models.user_models import User

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_validate_username_unique(self):
        """Ensure validate_username raises an error if username already exists."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_username('existinguser')

    def test_validate_username_unique_new(self):
        """Ensure validate_username allows a new unique username."""
        serializer = UserSerializer()
        self.assertEqual(serializer.validate_username('newuser'), 'newuser')

    def test_validate_email_unique(self):
        """Ensure validate_email raises an error if email already exists."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_email('existinguser@example.com')

    def test_validation_email_unique_new(self):
        """Ensure validation_email allows a new unique email."""
        serializer = UserSerializer()
        self.assertEqual(serializer.validate_email('new@example.com'), 'new@example.com')

    def test_validate_name_fields(self):
        """Ensure validate_name_fields raises an error if first_name or last_name is empty."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_name_fields({'first_name':'', 'last_name':'Doe'})
        with self.assertRaises(ValidationError):
            serializer.validate_name_fields({'first_name':'John', 'last_name':''})

    def test_validate_name_fields_valid(self):
        """Ensure validation_name_fields allows non-empty names."""
        serializer = UserSerializer()
        data = {'first_name':'John', 'last_name':'Doe'}
        self.assertEqual(serializer.validate_name_fields(data), data)

    def test_update_user(self):
        """Ensure update_user correctly updates user attributes."""
        serializer = UserSerializer()
        updated_data = {'first_name':'Jane', 'last_name':'Smith'}
        updated_user = serializer.update_user(self.user, updated_data)
        self.assertEqual(updated_user.first_name, 'Jane')
        self.assertEqual(updated_user.last_name, 'Smith')

    def test_delete_user(self):
        """Ensure delete_user removes the user from the database."""
        serializer = UserSerializer()
        response = serializer.delete_user(self.user)
        self.assertEqual(response, {'message':'User account deleted successfully.'})
        self.assertFalse(User.objects.filter(id=self.user.id).exists())