from django.test import TestCase
from redis import ResponseError
from users.models.user_models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models.profile_models import UserProfile, Experience
from listings.models.listings_models import Listing, Availability, Day
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



class DayViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            first_name='John',
            last_name='Doe'
        )
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
            completion_status=True,
            availability=self.availability
        )

        self.url = reverse('days-list')
        self.url_detail= reverse('days-detail', args=[self.listing.pk])

    
    def test_get_days_for_own_listing(self):
        """Test that a user can retrieve days for their listing."""
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?listing={self.listing.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['day_of_week'], 'monday')
        self.assertEqual(self.monday.start_time, '09.00')
        self.assertEqual(self.monday.end_time, '17.00')


    def test_get_days_other_users_listing(self):
        """Test that another user can retrieve another user listing availability days."""
        self.client.force_authenticate(self.user2)
        response = self.client.get(f"{self.url}?listing={self.listing.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_update_own_day_availability(self):
        """Test that a user can update the day availabilities of their listing."""
        self.client.force_authenticate(self.user)
        updated_data={
            'day_of_week':'monday',
            'is_available':True,
            'start_time':'09.00',
            'end_time':'18.00',
        }
        response = self.client.patch(f"{self.url_detail}?listing={self.listing.id}", updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.monday.refresh_from_db()
        self.assertEqual(self.monday.start_time.strftime('%H:%M'), '09:00')
        self.assertEqual(self.monday.end_time.strftime('%H:%M'), '18:00')

    def test_cannot_update_other_users_day(self):
        """Test that a user cannot update a day for another user's lising."""
        self.client.force_authenticate(self.user2)
        updated_data={
            'day_of_week':'monday',
            'is_available':True,
            'start_time':'09.00',
            'end_time':'18.00',
        }
        response = self.client.patch(f"{self.url_detail}?listing={self.listing.id}", updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_create_new_day(self):
        """Test that users cannot manually create new days."""
        self.client.force_authenticate(self.user)
        create_data = {
            'day_of_week':'monday',
            'is_available':True,
            'start_time':'09.00',
            'end_time':'18.00',
        }
        response = self.client.post(self.url, create_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_delete_day(self):
        """Test users cannot delete existing days."""
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unauthenticated_access_success(self):
        """Test that unauthenticated users can access to the days availability."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AvailabilityViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            first_name='John',
            last_name='Doe'
        )
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
        self.monday = Day.objects.create(
            day_of_week='monday',
            is_available=True,
            start_time='09.00',
            end_time='17.00',
        )
        self.availability = Availability.objects.create(
            monday=self.monday,
        )
        self.listing = Listing.objects.create(
            user_profile=self.user_profile,
            pricing_per_hour=50.0,
            service_description ='Talk about web designing.',
            completion_status=True,
            availability=self.availability
        )
        self.url = reverse('availabilities-list')
        self.url_detail= reverse('availabilities-detail', args=[self.listing.pk])

    def test_get_queryset_with_own_listing(self):
        """Test retrieving availabilities for user's own listing."""
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?listing={self.listing.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_queryset_unauthenticated(self):
        """Test retrieving availabilities for when a user is not registered or authenticated."""
        response = self.client.get(f"{self.url}?listing={self.listing.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_availability_duplicate(self):
        """Test that one listing can only have one availability."""
        self.client.force_authenticate(self.user)
        data = {
            'listing': self.listing.id,  
            'monday': {'is_available': True, 'start_time': '09.00', 'end_time': '17.00'}
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Availability.objects.count(), 1)
        self.assertEqual(response.data['error'], 'Availability for this listing already exists.')

    def test_create_availability_without_listing(self):
        """Test creating availability without a specific listing."""
        self.client.force_authenticate(self.user)
        data = {  
            'monday': {'is_available': True, 'start_time': '09.00', 'end_time': '17.00'}
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Listing is required')

    def test_create_availability_unauthorized_listing(self):
        """Test creating availability for another user's listing."""
        self.client.force_authenticate(self.user2)
        data = {
            'listing': self.listing.id,  
            'monday': {'is_available': True, 'start_time': '09.00', 'end_time': '17.00'}
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Listing does not exist.')

    def test_update_availability_success(self):
        """Test updating the availability for own listing."""
        self.client.force_authenticate(self.user)
        updated_data={
            'monday': {'is_available': True, 'start_time': '10.00', 'end_time': '17.00'}
        }
        response = self.client.patch(self.url_detail, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.availability.refresh_from_db()
        self.assertEqual(str(self.availability.monday.start_time), '10:00:00')

    def test_update_availability_listing_forbidden(self):
        """Test attempting to update another user's availability."""
        self.client.force_authenticate(self.user2)
        updated_data={
            'monday': {'is_available': True, 'start_time': '10.00', 'end_time': '17.00'}
        }
        response = self.client.patch(self.url_detail, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.availability.refresh_from_db()
        self.assertEqual(str(self.availability.monday.start_time), '09:00:00')

    
