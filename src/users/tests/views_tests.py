from urllib import response
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from io import BytesIO
from PIL import Image
import json
from users.views.profile_views import (
    UserProfileViewSet,
    ExperienceViewSet,
    CareerViewSet,
    EducationViewSet,
    ReviewViewSet
)
from users.models.profile_models import (
    UserProfile,
    Experience,
    Career,
    Education,
    Review
)

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


class UserProfileViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            country='USA',
            job_title='Developer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating=4.5,
            description="Experience software engineer specializing in Django."
        )
        self.url = reverse('user_profile-list')
        self.client.force_authenticate(self.user)

    def test_list_user_profiles_with_filters(self):
        """Tests listing user profiles with country and job_title filters."""
        response = self.client.get(self.url, {'country': 'USA', 'job_title': 'Developer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_user_profile(self):
        """Tests retrieving a single user profile."""
        url = f"{self.url}{self.profile.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_profile(self):
        """Tests creating a new user profile."""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password123',
            first_name='new',
            last_name='user',
        )
        self.assertFalse(UserProfile.objects.filter(user=new_user).exists())

        image = Image.new('RGB', (100, 100), color = (255, 0, 0))  # Red image
        image_file = BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0) 
        profile_picture = SimpleUploadedFile(
            'test_image.jpg', 
            image_file.read(),  
            content_type='image/jpeg'  
        )
        data = {
            'user': str(new_user.pk), 
            'country': 'USA',
            'job_title': 'Developer',
            'company_name': 'TechCorp',
            'total_meetings': 5,
            'meetings_completed': 4,
            'total_minutes': 300,
            'rating': 4.5,
            'description': "Experienced software engineer specializing in Django.",
            'profile_picture': profile_picture
        }
        self.client.force_authenticate(user=new_user)
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())

    def test_update_user_profile(self):
        """Tests updating the user profile(only the owner can update)."""
        url = f"{self.url}{self.profile.pk}/"
        data = {'country': 'Canada'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile_forbidden(self):
        """Tests that a non-owner cannot update a profile."""
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password123',
            first_name='Another',
            last_name='User',
        )
        another_profile = UserProfile.objects.create(user=another_user)
        url = f"{self.url}{self.profile.pk}/"
        data = {'country': 'Canada'}
        self.client.force_authenticate(user=another_user)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_profile(self):
        """Test deleting a user profile(only the owner can delete)."""
        url = f"{self.url}{self.profile.pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_user_profile_forbidden(self):
        """Test that a non-owner cannot delete a profile."""
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password123',
            first_name='Another',
            last_name='User',
        )
        another_profile = UserProfile.objects.create(user=another_user)
        url = f"{self.url}{self.profile.pk}/"
        self.client.force_authenticate(user=another_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_experiences(self):
        """Tests listing experiences related to a user profile."""
        url = f"{self.url}{self.profile.pk}/experiences/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_statistics(self):
        """Tests updating user profile statistics(only the owner can update)."""
        url = f"{self.url}{self.profile.pk}/update_statistics/"
        data  = {
            'total_meetings':10,
            'meetings_completed':8,
            'total_minutes':500,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_statistics_forbidden(self):
        """Test that a non-owner cannot update statistics for a user profile."""
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password123',
            first_name='Another',
            last_name='User',
        )
        another_profile = UserProfile.objects.create(user=another_user)
        url = f"{self.url}{self.profile.pk}/update_statistics/"
        data = {
            'total_meetings':10,
            'meetings_completed':8,
            'total_minutes':500,
        }
        self.client.force_authenticate(user=another_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_careers(self):
        """Tests listing careers related to a user profile."""
        url = f"{self.url}{self.profile.pk}/careers/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        

class ExperienceViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.user_profile = UserProfile.objects.create(user=self.user, country='USA', job_title='Developer')
        self.experience_data = {
            'name': 'WebDesign',
            'weight': 1,
        }
        self.url = reverse('user_experiences-list')
        self.client.force_authenticate(self.user)

    def test_create_experience(self):
        """Test creating an experience for an authenticated user."""
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, self.experience_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(Experience.objects.first().user_profile, self.user_profile)

    def test_create_experience_without_profile(self):
        """Test creating an experience when the user does not have a profile."""
        user_without_profile = User.objects.create_user(
            username='userwitout',
            email='userwitout@example.com',
            password='password123',
            first_name='User',
            last_name='Without',
        )
        self.client.force_authenticate(user_without_profile)
        response = self.client.post(self.url, self.experience_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], "You must create a profile before adding experiences.")

    def test_update_experience(self):
        """Test updating an experience by the owner. Ensures that only the owner can update it."""
        experience = Experience.objects.create(user_profile=self.user_profile, **self.experience_data)
        updated_data = {'name': 'WebDev','weight': 2,}
        self.client.force_authenticate(self.user)
        response = self.client.put(f"{self.url}{experience.id}/", updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        experience.refresh_from_db()
        self.assertEqual(experience.name, 'WebDev')

    def test_update_experience_without_experience(self):
        """Test updating an expeirence by a user who does not own the experience."""
        experience = Experience.objects.create(user_profile=self.user_profile, **self.experience_data)
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='password123',
            first_name='Other',
            last_name='User',
        )
        other_user_profile = UserProfile.objects.create(user=other_user)
        self.client.force_authenticate(other_user)
        updated_data = {'name': 'WebDev','weight': 2,}
        response = self.client.put(f"{self.url}{experience.id}/", updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You do not have permission to access this experience.", response.data['detail'])

    def test_delete_experience(self):
        """Test deleting an experience by the owner."""
        experience = Experience.objects.create(user_profile=self.user_profile, **self.experience_data)
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"{self.url}{experience.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Experience.objects.count(), 0)

    def test_delete_experience_without_permission(self):
        """"Test deleting an experience by a user who does not own the experience."""
        experience = Experience.objects.create(user_profile=self.user_profile, **self.experience_data)
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='password123',
            first_name='Other',
            last_name='User',
        )
        other_user_profile = UserProfile.objects.create(user=other_user)
        self.client.force_authenticate(other_user)
        response = self.client.delete(f"{self.url}{experience.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You do not have permission to access this experience.", str(response.data['detail']))

    def test_list_experiences(self):
        """Test listing experiences for the authenticated user."""
        Experience.objects.create(user_profile=self.user_profile, **self.experience_data)
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CareerViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.user_profile = UserProfile.objects.create(user=self.user, country='USA', job_title='Developer')
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otherusert@example.com',
            password='password123',
            first_name='Other',
            last_name='User',
        )
        self.other_user_profile = UserProfile.objects.create(user=self.other_user, country='USA', job_title='Developer')
        self.career = Career.objects.create(
            user_profile = self.user_profile,
            job_title = 'Developer',
            company_name = 'TechCorp',
            job_status = 'full-time',
            description = 'Developer at TechCorp',
        )
        self.url = reverse('user_careers-list')
        self.client.force_authenticate(self.user)

    def test_list_careers(self):
        """Test listing careers only for the authenticated user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1 )

    def test_create_career_with_profile(self):
        """Test creating a career when the user has a profile."""
        data = {'job_title':'Developer', 'company_name': 'TechCorp', 'job_status': 'full-time', 'description':'Developer at TechCorp'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_career_without_profile(self):
        """Test creating a career when the user does not have a profile."""
        self.no_profile_user = User.objects.create_user(
            username='noprofileuser',
            email='noprofileuser@example.com',
            password='password123',
            first_name='Noprofile',
            last_name='User',
        )
        self.client.force_authenticate(self.no_profile_user)
        data = {'job_title':'Developer', 'company_name': 'TechCorp', 'job_status': 'full-time', 'description':'Developer at TechCorp'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You must create a profile before adding careers.", str(response.data))

    def test_retrieve_career_owner(self):
        """Test retrieving a career as the owner."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_career_not_owner(self):
        """Test retrieving a career as a non-owner should fail."""
        self.client.force_authenticate(self.other_user)
        response = self.client.get(f"{self.url}{self.career.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You do not have permission to access this career.", response.data['detail'])
    
    def test_update_career_owner(self):
        """Test updating a career as the owner."""
        data = {'job_title':'Designer',  'company_name': 'TechCorp', 'job_status': 'full-time', 'description':'Developer at TechCorp'}
        response = self.client.put(f"{self.url}{self.career.id}/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.career.refresh_from_db()
        self.assertEqual(self.career.job_title, 'Designer')

    def test_update_career_not_owner(self):
        """Test updating a career as a non-owner should fail."""
        self.client.force_authenticate(self.other_user)
        data = {'job_title':'Designer',  'company_name': 'TechCorp', 'job_status': 'full-time', 'description':'Developer at TechCorp'}
        response = self.client.put(f"{self.url}{self.career.id}/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_career_owner(self):
        """Test deleting a career as the owner."""
        response = self.client.delete(f"{self.url}{self.career.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Career.objects.filter(id=self.career.id).exists())

    def test_delete_career_not_owner(self):
        """Test deleting a career as a non-owner should fail."""
        self.client.force_authenticate(self.other_user)
        response = self.client.delete(f"{self.url}{self.career.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    

