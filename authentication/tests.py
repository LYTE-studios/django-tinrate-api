from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

from .models import RefreshToken as CustomRefreshToken
from users.models import EmailVerification

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """Test cases for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.register_url = reverse('authentication:register')
        self.login_url = reverse('authentication:login')
        self.logout_url = reverse('authentication:logout')
        self.verify_email_url = reverse('authentication:verify_email')
        self.resend_verification_url = reverse('authentication:resend_verification')
        
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'firstName': 'Test',
            'lastName': 'User',
            'country': 'US'
        }
    
    def test_user_registration_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], self.user_data['email'])
        self.assertTrue(response.data['data']['requiresEmailVerification'])
        
        # Check user was created
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['firstName'])
        self.assertEqual(user.last_name, self.user_data['lastName'])
        self.assertFalse(user.is_email_verified)
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create user first
        User.objects.create_user(
            email=self.user_data['email'],
            password='password123'
        )
        
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_user_registration_invalid_data(self):
        """Test registration with invalid data."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_user_login_success(self):
        """Test successful user login."""
        # Create and verify user
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['firstName'],
            last_name=self.user_data['lastName'],
            is_email_verified=True
        )
        
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('accessToken', response.data['data'])
        self.assertIn('refreshToken', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], user.email)
    
    def test_user_login_unverified_email(self):
        """Test login with unverified email."""
        # Create unverified user
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_email_verified=False
        )
        
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_email_verification_success(self):
        """Test successful email verification."""
        # Create user and verification code
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        verification = EmailVerification.objects.create(
            user=user,
            verification_code='123456',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        verify_data = {
            'email': user.email,
            'verificationCode': '123456'
        }
        
        response = self.client.post(self.verify_email_url, verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check user is verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        # Check verification is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)
    
    def test_email_verification_invalid_code(self):
        """Test email verification with invalid code."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        verify_data = {
            'email': user.email,
            'verificationCode': '999999'
        }
        
        response = self.client.post(self.verify_email_url, verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_resend_verification_success(self):
        """Test successful resend verification."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_email_verified=False
        )
        
        resend_data = {
            'email': user.email
        }
        
        response = self.client.post(self.resend_verification_url, resend_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check verification code was created
        self.assertTrue(
            EmailVerification.objects.filter(user=user).exists()
        )
    
    def test_logout_success(self):
        """Test successful logout."""
        # Create and login user
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_email_verified=True
        )
        
        # Create refresh token
        refresh_token = CustomRefreshToken.create_for_user(user)
        
        # Authenticate user
        jwt_refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_refresh.access_token}')
        
        logout_data = {
            'refreshToken': refresh_token.token
        }
        
        response = self.client.post(self.logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check refresh tokens are revoked
        self.assertFalse(
            CustomRefreshToken.objects.filter(
                user=user,
                is_revoked=False
            ).exists()
        )


class RefreshTokenModelTestCase(TestCase):
    """Test cases for RefreshToken model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = CustomRefreshToken.create_for_user(self.user)
        
        self.assertEqual(token.user, self.user)
        self.assertIsNotNone(token.token)
        self.assertFalse(token.is_revoked)
        self.assertTrue(token.is_valid())
    
    def test_refresh_token_expiration(self):
        """Test refresh token expiration."""
        token = CustomRefreshToken.objects.create(
            user=self.user,
            token='test_token',
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )
        
        self.assertTrue(token.is_expired())
        self.assertFalse(token.is_valid())
    
    def test_refresh_token_revocation(self):
        """Test refresh token revocation."""
        token = CustomRefreshToken.create_for_user(self.user)
        
        self.assertTrue(token.is_valid())
        
        token.revoke()
        
        self.assertTrue(token.is_revoked)
        self.assertFalse(token.is_valid())


class EmailVerificationModelTestCase(TestCase):
    """Test cases for EmailVerification model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_email_verification_creation(self):
        """Test creating email verification."""
        verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(verification.user, self.user)
        self.assertEqual(verification.verification_code, '123456')
        self.assertFalse(verification.is_used)
        self.assertTrue(verification.is_valid())
    
    def test_email_verification_expiration(self):
        """Test email verification expiration."""
        verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        self.assertTrue(verification.is_expired())
        self.assertFalse(verification.is_valid())
    
    def test_email_verification_usage(self):
        """Test email verification usage."""
        verification = EmailVerification.objects.create(
            user=self.user,
            verification_code='123456',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertTrue(verification.is_valid())
        
        verification.is_used = True
        verification.save()
        
        self.assertFalse(verification.is_valid())
