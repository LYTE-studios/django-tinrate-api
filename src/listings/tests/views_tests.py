from django.test import TestCase
from redis import ResponseError
from users.models.user_models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models.profile_models import UserProfile, Experience
from listings.models.listings_models import Listing
from listings.serializers.listings_serializers import ListingSerializer

class ListingViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.experience = Experience.objects.create(name='Designer', weight=2)
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            country='USA',
            job_title='Designer',
            company_name='TechCorp',
            profile_picture=None,
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            first_name='Jane',
            last_name='Doe'
        )
        self.user_profile2 = UserProfile.objects.create(
            user=self.user2,
            country='USA',
            job_title='Designer',
            company_name='TechCorp',
            profile_picture=None,
        )
        self.no_profile_user = User.objects.create_user(
            username='user3',
            email='use3@example.com',
            first_name='Johny',
            last_name='Doe'
        )
        self.completed_listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            availability={'days':'Mon-Fri', 'start-time':'09.00', 'end_time':'17.00'},
            completion_status=True,
            experience=self.experience
        )
        self.incomplete_listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            availability={'days':'Mon-Fri', 'start-time':'09.00', 'end_time':'17.00'},
            completion_status=False,
            experience=self.experience
        )
        self.url = reverse('listings-list')
        self.url_detail= reverse('listings-detail', args=[self.completed_listing.pk])
        self.url_detail_incomplete= reverse('listings-detail', args=[self.incomplete_listing.pk])

    def test_list_listings_authenticated(self):
        """Test listing listings for an authenticated user."""
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_listings_with_filters(self):
        """Test listing listings with country and experience filters."""
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {
            'country':'USA',
            'experience':'Designer'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_own_listing(self):
        """Test retrieving the user's own listing."""
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.completed_listing.id)

    def test_retrieve_other_users_completed_listing(self):
        """Test retrieving another user's completed listing."""
        self.client.force_authenticate(self.user2)
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_users_incomplete_listing(self):
        """Test attempting to retrieve another user's incomplete listing."""
        self.client.force_authenticate(self.user2)
        response = self.client.get(self.url_detail_incomplete)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_listing(self):
        """Test creating a new listing."""
        self.client.force_authenticate(self.user)
        listing_data = {
            "pricing_per_hour": 60.0,
            "service_description": "Web development services.",
            "availability": {"days": "Mon-Fri", "start_time": "09:00", "end_time": "18:00"},
            "completion_status": False,
            "experience": self.experience.id,
        }
        response = self.client.post(self.url, listing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['completion_status'])
        self.assertEqual(response.data['user_profile'], self.user_profile.id)

    def test_create_listing_without_profile(self):
        """Test creating a listing when user profile doesn't exist."""
        self.client.force_authenticate(self.no_profile_user)
        listing_data = {
            "pricing_per_hour": 60.0,
            "service_description": "Web development services.",
            "availability": {"days": "Mon-Fri", "start_time": "09:00", "end_time": "18:00"},
            "completion_status": False,
            "experience": self.experience.id,
        }
        response = self.client.post(self.url, listing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_update_own_listing(self):
        """Test updating the user's own listing completed."""
        self.client.force_authenticate(self.user)
        updated_data = {
            "pricing_per_hour": 60.0,
        }
        response = self.client.patch(self.url_detail, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['pricing_per_hour']), 60.00)

    def test_update_own_listing_incomplete(self):
        """Test updating the user's own listing incomplete."""
        self.client.force_authenticate(self.user)
        updated_data = {
            "pricing_per_hour": 60.0,
        }
        response = self.client.patch(self.url_detail_incomplete, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['pricing_per_hour']), 60.00)

    def test_update_other_users_listing(self):
        """Test attempting to update another user's listing."""
        self.client.force_authenticate(self.user2)
        updated_data={
            "pricing_per_hour": 60.0,
        }
        response = self.client.patch(self.url_detail_incomplete, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleting_own_listing(self):
        """Test deleting the user's own listing incomplete."""
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url_detail_incomplete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Listing.objects.filter(id=self.incomplete_listing.id).exists())

    def test_deleting_own_listing(self):
        """Test deleting the user's own listing complete."""
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Listing.objects.filter(id=self.completed_listing.id).exists())

    def test_deleting_other_users_listing(self):
        """Test attempting to delete another user's listing."""
        self.client.force_authenticate(self.user2)
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users can access the viewset but cannot create, update or delete."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        updated_data={
            "pricing_per_hour": 60.0,
        }
        response = self.client.patch(self.url_detail_incomplete, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



