from datetime import time
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models.profile_models import UserProfile, Review, Experience
from listings.models.listings_models import Listing, Day, Availability
from listings.serializers.listings_serializers import ListingSerializer, DaySerializer, AvailabilitySerializer
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
        self.url_detail= reverse('listings-detail', args=[self.listing.pk])
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


    def test_listing_view_get_total_reviews(self):
        """Test the listing view returns the correct total_reviews field."""
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reviews'], 2)

    def test_create_listing_invalid_data(self):
        """Test creating a listing with missing required fields."""
        data = {
            'pricing_per_hour':60.0
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('availability', response.data)


class DaySerializerTest(TestCase):
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
        self.monday = Day.objects.create(
            day_of_week='monday',
            is_available=True,
            start_time='09.00',
            end_time='17.00',
        )
        self.tuesday = Day.objects.create(
            day_of_week='tuesday',
            is_available=True,
            start_time='12.00',
            end_time='20.00',
        )
        self.availability = Availability.objects.create(
            monday=self.monday,
            tuesday=self.tuesday
        )
        self.listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            availability=self.availability,
            completion_status=False,
            experience=self.experience
        )
    
    def test_valid_serializer_data(self):
        """Test serializer validation with valid data."""
        serializer = DaySerializer(data={
            'is_available':True,
            'start_time':'09.00',
            'end_time':'17.00',
        })
        self.assertTrue(serializer.is_valid(), f"Serializer error: {serializer.errors}")

    def test_unavailable_day_validation(self):
        """Test serializer validation for an unavailable day."""
        serializer = DaySerializer(data={
            'is_available':False,   
        })
        self.assertTrue(serializer.is_valid(), f"Serializer error: {serializer.errors}")

    def test_missing_time_when_available(self):
        """Test validation fail when time is missing for an available day."""
        serializer = DaySerializer(data={
            'is_available':True,   
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('time', serializer.errors)
        self.assertEqual(serializer.errors['time'][0], 'Both start_time and end_time are required when availability is True')

    def test_invalid_time_order(self):
        """Test validation fail when start_time is later than or equal to end_time."""
        serializer = DaySerializer(data={
            'is_available':True,
            'start_time':'14.00',
            'end_time':'09.00',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('time', serializer.errors)
        self.assertEqual(serializer.errors['time'][0],'Start time must be before end time.')

    def test_serializer_read_only_fields(self):
        """Test that read-only fileds cannot be modified."""
        original_day_of_week = self.monday.day_of_week
        serializer = DaySerializer(self.monday, data={
            'day_of_week':'Monday',
            'is_available':False
        }, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_day = serializer.save()
        self.assertEqual(updated_day.day_of_week, original_day_of_week)

    def test_serializer_update(self):
        """Test updating an existing Day instance."""
        serializer = DaySerializer(self.monday, data={
            'is_available':False,
            'start_time': None,
            'end_time':None,
        }, partial=True)
        self.assertTrue(serializer.is_valid(), f"Serializer errors:{serializer.errors}")
        updated_day = serializer.save()
        self.assertFalse(updated_day.is_available)
        self.assertIsNone(updated_day.start_time)
        self.assertIsNone(updated_day.end_time)

    def test_serializer_representation(self):
        """Test the serializer's data representation."""
        serializer = DaySerializer(self.monday)
        data = serializer.data
        self.assertEqual(data['day_of_week'], 'monday')
        self.assertEqual(data['is_available'], True)
        self.assertEqual(data['start_time'],'09.00')
        self.assertEqual(data['end_time'], '17.00')

   
class AvailabilitySerializerTest(TestCase):
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
        self.monday = Day.objects.create(
            day_of_week='monday',
            is_available=True,
            start_time='09.00',
            end_time='17.00',
        )
        self.tuesday = Day.objects.create(
            day_of_week='tuesday',
            is_available=True,
            start_time='12.00',
            end_time='20.00',
        )
        self.availability = Availability.objects.create(
            monday=self.monday,
            tuesday=self.tuesday,
        )
        self.listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            availability=self.availability,
            completion_status=False,
            experience=self.experience
        )
    
    def test_create_availability_with_partial_week(self):
        """Test creating an availability with only some days set."""
        availability_data = {
            'listing': self.listing,
            'monday': {
                'id': self.monday.id,
                'day_of_week': self.monday.day_of_week,
                'is_available': self.monday.is_available,
                'start_time': self.monday.start_time,
                'end_time': self.monday.end_time,
            },
            'tuesday': {
                'id': self.tuesday.id,
                'day_of_week': self.tuesday.day_of_week,
                'is_available': self.tuesday.is_available,
                'start_time': self.tuesday.start_time,
                'end_time': self.tuesday.end_time,
            },
        }
        serializer = AvailabilitySerializer(data=availability_data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
    
    def test_create_no_availability(self):
        """Test validation fail when no days are available."""
        availability_data = {
            'listing': self.listing,
            'monday': {'is_available': False},
            'tuesday': {'is_available': False},
            'wednesday': {'is_available': False},
            'thursday': {'is_available': False},
            'friday': {'is_available': False},
            'saturday': {'is_available': False},
            'sunday': {'is_available': False}
        }
        serializer = AvailabilitySerializer(data=availability_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('availability', serializer.errors)
        self.assertEqual(serializer.errors['availability'][0], 'At least one day must be available.')

    def test_create_duplicate_availability_listing(self):
        """Test that creating multiple availabilities for the same listing is prevented."""
        self.availability = Availability.objects.create(
            monday=self.monday,
            tuesday=self.tuesday,
        )
        first_serializer = AvailabilitySerializer(data=self.availability)
        self.assertFalse(first_serializer.is_valid())
        
    def test_update_availability(self):
        """Test updating an existing availability."""
        initial_data = {
            'listing': self.listing.id,  
            'monday': {'is_available': True, 'start_time': '09.00', 'end_time': '17.00'}
        }
        initial_serializer = AvailabilitySerializer(data=initial_data)
        initial_serializer.is_valid()
        availability = initial_serializer.save()
        

        