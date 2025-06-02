from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerification

User = get_user_model()


class UserModelTestCase(TestCase):
    """Test cases for User model."""
    
    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            country='US'
        )
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.country, 'US')
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.profile_complete)
        self.assertFalse(user.is_expert)
        self.assertTrue(user.check_password('testpassword123'))
    
    def test_user_full_name_property(self):
        """Test user full_name property."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.full_name, 'Test User')
    
    def test_mark_profile_complete(self):
        """Test marking profile as complete."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            country='US'
        )
        
        user.mark_profile_complete()
        
        self.assertTrue(user.profile_complete)
    
    def test_mark_profile_complete_incomplete_data(self):
        """Test marking profile as complete with incomplete data."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test'
            # Missing last_name and country
        )
        
        user.mark_profile_complete()
        
        self.assertFalse(user.profile_complete)


class UserAPITestCase(APITestCase):
    """Test cases for User API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            country='US',
            is_email_verified=True,
            profile_complete=True
        )
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.user_profile_url = reverse('users:user_profile')
        self.complete_profile_url = reverse('users:complete_profile')
        self.user_stats_url = reverse('users:get_user_stats')
    
    def test_get_current_user(self):
        """Test getting current user profile."""
        response = self.client.get(self.user_profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], self.user.email)
        self.assertEqual(response.data['data']['user']['firstName'], self.user.first_name)
    
    def test_get_current_user_unauthenticated(self):
        """Test getting current user without authentication."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.get(self.get_user_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_current_user(self):
        """Test updating current user profile."""
        update_data = {
            'firstName': 'Updated',
            'lastName': 'Name',
            'country': 'CA'
        }
        
        response = self.client.put(self.update_user_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['firstName'], 'Updated')
        self.assertEqual(response.data['data']['user']['lastName'], 'Name')
        self.assertEqual(response.data['data']['user']['country'], 'CA')
        
        # Check user was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.country, 'CA')
    
    def test_update_current_user_partial(self):
        """Test partial update of current user profile."""
        update_data = {
            'firstName': 'PartialUpdate'
        }
        
        response = self.client.put(self.update_user_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['firstName'], 'PartialUpdate')
        # Other fields should remain unchanged
        self.assertEqual(response.data['data']['user']['lastName'], self.user.last_name)
    
    def test_complete_profile_already_complete(self):
        """Test completing profile when already complete."""
        complete_data = {
            'firstName': 'Complete',
            'lastName': 'User',
            'country': 'US'
        }
        
        response = self.client.post(self.complete_profile_url, complete_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_complete_profile_success(self):
        """Test successful profile completion."""
        # Create incomplete user
        incomplete_user = User.objects.create_user(
            email='incomplete@example.com',
            password='testpassword123',
            is_email_verified=True,
            profile_complete=False
        )
        
        # Authenticate incomplete user
        refresh = RefreshToken.for_user(incomplete_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        complete_data = {
            'firstName': 'Complete',
            'lastName': 'User',
            'country': 'US'
        }
        
        response = self.client.post(self.complete_profile_url, complete_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['firstName'], 'Complete')
        
        # Check user profile is marked as complete
        incomplete_user.refresh_from_db()
        self.assertTrue(incomplete_user.profile_complete)
    
    def test_get_user_stats(self):
        """Test getting user statistics."""
        response = self.client.get(self.user_stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        stats = response.data['data']
        self.assertIn('profileComplete', stats)
        self.assertIn('isEmailVerified', stats)
        self.assertIn('isExpert', stats)
        self.assertIn('memberSince', stats)
        self.assertIn('clientStats', stats)
    
    def test_upload_profile_image(self):
        """Test uploading profile image."""
        upload_url = reverse('users:upload_profile_image')
        image_data = {
            'imageUrl': 'https://example.com/profile.jpg'
        }
        
        response = self.client.post(upload_url, image_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check user profile image was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_image_url, 'https://example.com/profile.jpg')
    
    def test_upload_profile_image_no_url(self):
        """Test uploading profile image without URL."""
        upload_url = reverse('users:upload_profile_image')
        
        response = self.client.post(upload_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_change_email(self):
        """Test changing user email."""
        change_email_url = reverse('users:change_email')
        email_data = {
            'email': 'newemail@example.com'
        }
        
        response = self.client.post(change_email_url, email_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['requiresEmailVerification'])
        
        # Check user email was updated and verification reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertFalse(self.user.is_email_verified)
    
    def test_change_email_duplicate(self):
        """Test changing email to existing email."""
        # Create another user
        User.objects.create_user(
            email='existing@example.com',
            password='testpassword123'
        )
        
        change_email_url = reverse('users:change_email')
        email_data = {
            'email': 'existing@example.com'
        }
        
        response = self.client.post(change_email_url, email_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_delete_account(self):
        """Test deleting user account."""
        delete_url = reverse('users:delete_account')
        
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check user is deactivated
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class EmailVerificationModelTestCase(TestCase):
    """Test cases for EmailVerification model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_email_verification_str(self):
        """Test EmailVerification string representation."""
        verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at='2025-01-01 00:00:00+00:00'
        )
        
        expected_str = f"Verification for {self.user.email}"
        self.assertEqual(str(verification), expected_str)
    
    def test_email_verification_is_expired(self):
        """Test EmailVerification is_expired method."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create expired verification
        expired_verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        # Create valid verification
        valid_verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='654321',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertTrue(expired_verification.is_expired())
        self.assertFalse(valid_verification.is_expired())
    
    def test_email_verification_is_valid(self):
        """Test EmailVerification is_valid method."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create valid verification
        valid_verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=False
        )
        
        # Create used verification
        used_verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='654321',
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=True
        )
        
        # Create expired verification
        expired_verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='789012',
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )
        
        self.assertTrue(valid_verification.is_valid())
        self.assertFalse(used_verification.is_valid())
        self.assertFalse(expired_verification.is_valid())
