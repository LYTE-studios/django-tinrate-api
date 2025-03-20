from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class UserViewTest(APITestCase):
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.url = reverse('user_view')

    def test_get_user_authenticated(self):
        """Test that authenticated users can get their information."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_get_user_unauthenticated(self):
        """Test that unauthenticated users cannot get their information."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_success(self):
        """Test successful user update."""
        self.client.force_authenticate(user=self.user)
        updated_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }

        response = self.client.put(
           self.url,
           data=json.dumps(updated_data),
           content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_update_user_invalid_data(self):
        """Test user update with invalid data."""
        self.client.force_authenticate(user=self.user)
        invalid_data={'first_name':'',}
        response = self.client.put(
           self.url,
           data=json.dumps(invalid_data),
           content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_username_already_exists(self):
        """Test that updating username to existing one fails."""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)
        data = {'username':'existinguser',}
        response = self.client.put(
           self.url,
           data=json.dumps(data),
           content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_delete_user(self):
        """Test deleting a user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(username='testuser').exists())