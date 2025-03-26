from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models.profile_models import UserProfile, Review, Experience
from listings.models.listings_models import Listing
from listings.serializers.listings_serializers import ListingSerializer
from users.models.user_models import User
from django.urls import reverse

class ListingSerializerTest(TestCase):
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
        self.listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            availability={'days':'Mon-Fri', 'start-time':'09.00', 'end_time':'17.00'},
            completion_status=False,
            experience=self.experience
        )
        self.review1 = Review.objects.create(
            user_profile=self.user_profile,
            reviewer=self.user2,
            rating=4.5,
            comment='Great service!'
        )
        self.review2 = Review.objects.create(
            user_profile=self.user_profile,
            reviewer=self.user2,
            rating=5.0,
            comment='Great service!'
        )
        self.url = reverse('listings-list')
        self.url_detail= reverse('listings-detail', args=[self.listing.pk]) + '.json'
        self.client.force_authenticate(self.user)

    def test_total_reviews_calculation(self):
        """Test that the total_reviews is correctly calculated."""
        listing_data = {
            "id": self.listing.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "country": self.user_profile.country,
            "profile_picture": self.user_profile.profile_picture,
            "job_title": self.user_profile.job_title,
            "company_name": self.user_profile.company_name,
            "experience_name": self.experience.name,
            "pricing_per_hour": self.listing.pricing_per_hour,
            "service_description": self.listing.service_description,
            "availability": self.listing.availability,
            "completion_status": self.listing.completion_status,
            "rating": self.user_profile.rating,
            "total_reviews": 2, 
            "total_hours": 0,  
        }
        serializer = ListingSerializer(self.listing)
        self.assertEqual(serializer.data['total_reviews'], 2)

    def test_create_listing_with_required_fields(self):
        """Test creating a listing with all required fields and validate completion status."""
        data = {
            "pricing_per_hour": 60.0,
            "service_description": "Web development services.",
            "availability": {"days": "Mon-Fri", "start_time": "09:00", "end_time": "18:00"},
            "completion_status": False,
            "experience": self.experience.id,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(id=response.data['id'])
        self.assertFalse(listing.completion_status)

    def test_update_listing_completion_status(self):
        """Test updating a listing's completion status."""
        data = {
            "pricing_per_hour": 60.0,
            "service_description": "Web development services.",
            "availability": {"days": "Mon-Fri", "start_time": "09:00", "end_time": "18:00"},
            "completion_status": True,
            "experience": self.experience.id,
        }
        response = self.client.patch(self.url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing = Listing.objects.get(id=self.listing.id)
        self.assertTrue(listing.completion_status)