from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from .models import Expert, Availability
from users.models import User

User = get_user_model()


class ExpertModelTestCase(TestCase):
    """Test cases for Expert model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='expert@example.com',
            password='testpassword123',
            first_name='Expert',
            last_name='User',
            is_email_verified=True
        )
    
    def test_create_expert(self):
        """Test creating an expert."""
        expert = Expert.objects.create(
            user=self.user,
            title='UI/UX Designer',
            company='Test Company',
            bio='Expert in UI/UX design',
            hourly_rate=Decimal('50.00'),
            skills=['DESIGN', 'PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.user, self.user)
        self.assertEqual(expert.title, 'UI/UX Designer')
        self.assertEqual(expert.company, 'Test Company')
        self.assertEqual(expert.hourly_rate, Decimal('50.00'))
        self.assertEqual(expert.skills, ['DESIGN', 'PROGRAMMING'])
        self.assertEqual(expert.profile_url, 'expert-user')
        self.assertFalse(expert.is_listed)
    
    def test_expert_name_property(self):
        """Test expert name property."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.name, self.user.full_name)
    
    def test_expert_profile_image_url_property(self):
        """Test expert profile_image_url property."""
        self.user.profile_image_url = 'https://example.com/profile.jpg'
        self.user.save()
        
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.profile_image_url, 'https://example.com/profile.jpg')
    
    def test_expert_rating_property_no_reviews(self):
        """Test expert rating property with no reviews."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.rating, 0.0)
    
    def test_expert_review_count_property(self):
        """Test expert review_count property."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.review_count, 0)
    
    def test_expert_total_meetings_property(self):
        """Test expert total_meetings property."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.total_meetings, 0)
    
    def test_expert_total_meeting_time_property(self):
        """Test expert total_meeting_time property."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertEqual(expert.total_meeting_time, '00:00')
    
    def test_expert_publish_listing(self):
        """Test publishing expert listing."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
        
        self.assertFalse(expert.is_listed)
        
        expert.publish_listing()
        
        self.assertTrue(expert.is_listed)
    
    def test_expert_unpublish_listing(self):
        """Test unpublishing expert listing."""
        expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user',
            is_listed=True
        )
        
        self.assertTrue(expert.is_listed)
        
        expert.unpublish_listing()
        
        self.assertFalse(expert.is_listed)


class ExpertAPITestCase(APITestCase):
    """Test cases for Expert API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='expert@example.com',
            password='testpassword123',
            first_name='Expert',
            last_name='User',
            is_email_verified=True,
            profile_complete=True
        )
        
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpassword123',
            first_name='Client',
            last_name='User',
            is_email_verified=True
        )
        
        # Create expert
        self.expert = Expert.objects.create(
            user=self.user,
            title='UI/UX Designer',
            company='Test Company',
            bio='Expert in UI/UX design',
            hourly_rate=Decimal('50.00'),
            skills=['DESIGN', 'PROGRAMMING'],
            profile_url='expert-user',
            is_listed=True,
            is_featured=True
        )
        
        # Mark user as expert
        self.user.is_expert = True
        self.user.save()
        
        # URLs
        self.list_experts_url = reverse('experts:list_experts')
        self.featured_experts_url = reverse('experts:featured_experts')
        self.expert_detail_url = reverse('experts:get_expert_by_profile_url', kwargs={'profile_url': 'expert-user'})
        self.create_listing_url = reverse('experts:create_expert_listing')
        self.publish_listing_url = reverse('experts:publish_expert_listing')
        self.unpublish_listing_url = reverse('experts:unpublish_expert_listing')
    
    def test_list_experts_public(self):
        """Test listing experts (public endpoint)."""
        response = self.client.get(self.list_experts_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['experts']), 1)
        self.assertEqual(response.data['data']['experts'][0]['title'], 'UI/UX Designer')
        self.assertIn('pagination', response.data['data'])
    
    def test_list_experts_with_search(self):
        """Test listing experts with search query."""
        response = self.client.get(self.list_experts_url, {'search': 'UI/UX'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['experts']), 1)
    
    def test_list_experts_with_skills_filter(self):
        """Test listing experts with skills filter."""
        response = self.client.get(self.list_experts_url, {'skills': 'DESIGN'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['experts']), 1)
    
    def test_list_experts_with_price_filter(self):
        """Test listing experts with price filter."""
        response = self.client.get(self.list_experts_url, {'maxPrice': '100'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['experts']), 1)
        
        # Test with lower price filter
        response = self.client.get(self.list_experts_url, {'maxPrice': '25'})
        self.assertEqual(len(response.data['data']['experts']), 0)
    
    def test_featured_experts(self):
        """Test getting featured experts."""
        response = self.client.get(self.featured_experts_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['experts']), 1)
        self.assertEqual(response.data['data']['experts'][0]['title'], 'UI/UX Designer')
    
    def test_get_expert_by_profile_url(self):
        """Test getting expert by profile URL."""
        response = self.client.get(self.expert_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['expert']['title'], 'UI/UX Designer')
        self.assertIn('reviews', response.data['data'])
        self.assertIn('upcomingMeetings', response.data['data'])
    
    def test_get_expert_by_profile_url_not_found(self):
        """Test getting expert by non-existent profile URL."""
        url = reverse('experts:get_expert_by_profile_url', kwargs={'profile_url': 'nonexistent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_expert_listing_authenticated(self):
        """Test creating expert listing (authenticated)."""
        # Authenticate as a new user
        new_user = User.objects.create_user(
            email='newexpert@example.com',
            password='testpassword123',
            first_name='New',
            last_name='Expert',
            is_email_verified=True
        )
        
        refresh = RefreshToken.for_user(new_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        listing_data = {
            'title': 'Software Developer',
            'company': 'Tech Corp',
            'bio': 'Experienced software developer',
            'hourlyRate': '75.00',
            'skills': ['PROGRAMMING'],
            'profileUrl': 'new-expert'
        }
        
        response = self.client.post(self.create_listing_url, listing_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['expert']['title'], 'Software Developer')
        
        # Check user is marked as expert
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_expert)
    
    def test_create_expert_listing_unauthenticated(self):
        """Test creating expert listing without authentication."""
        listing_data = {
            'title': 'Software Developer',
            'company': 'Tech Corp',
            'bio': 'Experienced software developer',
            'hourlyRate': '75.00',
            'skills': ['PROGRAMMING'],
            'profileUrl': 'new-expert'
        }
        
        response = self.client.post(self.create_listing_url, listing_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_expert_listing(self):
        """Test updating existing expert listing."""
        # Authenticate as expert user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        update_data = {
            'title': 'Senior UI/UX Designer',
            'company': 'Updated Company',
            'bio': 'Updated bio',
            'hourlyRate': '60.00',
            'skills': ['DESIGN'],
            'profileUrl': 'expert-user'
        }
        
        response = self.client.post(self.create_listing_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['expert']['title'], 'Senior UI/UX Designer')
    
    def test_publish_expert_listing(self):
        """Test publishing expert listing."""
        # Create unpublished expert
        unpublished_expert = Expert.objects.create(
            user=self.client_user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='unpublished-expert',
            is_listed=False
        )
        self.client_user.is_expert = True
        self.client_user.save()
        
        # Authenticate as expert user
        refresh = RefreshToken.for_user(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.put(self.publish_listing_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['expert']['isListed'])
        
        # Check expert is published in database
        unpublished_expert.refresh_from_db()
        self.assertTrue(unpublished_expert.is_listed)
    
    def test_publish_expert_listing_no_profile(self):
        """Test publishing expert listing without expert profile."""
        # Authenticate as user without expert profile
        refresh = RefreshToken.for_user(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.put(self.publish_listing_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_unpublish_expert_listing(self):
        """Test unpublishing expert listing."""
        # Authenticate as expert user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.put(self.unpublish_listing_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check expert is unpublished in database
        self.expert.refresh_from_db()
        self.assertFalse(self.expert.is_listed)


class AvailabilityModelTestCase(TestCase):
    """Test cases for Availability model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='expert@example.com',
            password='testpassword123',
            first_name='Expert',
            last_name='User'
        )
        
        self.expert = Expert.objects.create(
            user=self.user,
            title='Developer',
            company='Test Company',
            bio='Test bio',
            hourly_rate=Decimal('50.00'),
            skills=['PROGRAMMING'],
            profile_url='expert-user'
        )
    
    def test_create_weekly_availability(self):
        """Test creating weekly availability."""
        availability = Availability.objects.create(
            expert=self.expert,
            weekday='monday',
            start_time='09:00',
            end_time='17:00',
            is_enabled=True,
            timezone='UTC'
        )
        
        self.assertEqual(availability.expert, self.expert)
        self.assertEqual(availability.weekday, 'monday')
        self.assertEqual(str(availability.start_time), '09:00:00')
        self.assertEqual(str(availability.end_time), '17:00:00')
        self.assertTrue(availability.is_enabled)
        self.assertIsNone(availability.date)
    
    def test_create_specific_date_availability(self):
        """Test creating specific date availability."""
        from datetime import date
        
        availability = Availability.objects.create(
            expert=self.expert,
            date=date(2025, 1, 15),
            start_time='10:00',
            end_time='16:00',
            is_available=True,
            timezone='UTC'
        )
        
        self.assertEqual(availability.expert, self.expert)
        self.assertEqual(availability.date, date(2025, 1, 15))
        self.assertEqual(str(availability.start_time), '10:00:00')
        self.assertEqual(str(availability.end_time), '16:00:00')
        self.assertTrue(availability.is_available)
        self.assertIsNone(availability.weekday)
    
    def test_availability_str_representation(self):
        """Test Availability string representation."""
        from datetime import date
        
        # Weekly availability
        weekly_availability = Availability.objects.create(
            expert=self.expert,
            weekday='monday',
            start_time='09:00',
            end_time='17:00',
            timezone='UTC'
        )
        
        expected_str = f"{self.expert.name} - monday 09:00:00-17:00:00"
        self.assertEqual(str(weekly_availability), expected_str)
        
        # Specific date availability
        date_availability = Availability.objects.create(
            expert=self.expert,
            date=date(2025, 1, 15),
            start_time='10:00',
            end_time='16:00',
            timezone='UTC'
        )
        
        expected_str = f"{self.expert.name} - 2025-01-15 10:00:00-16:00:00"
        self.assertEqual(str(date_availability), expected_str)
