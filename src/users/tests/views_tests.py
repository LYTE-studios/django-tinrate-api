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
            allow_cancellation_fee=False
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
        updated_date = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'allow_cancellation_fee': True,
        }

       
