from django.test import TestCase
from rest_framework.exceptions import ValidationError
from users import serializers
from users.serializers.user_serializer import UserSerializer
from users.models.user_models import User
from users.models.profile_models import UserProfile, Review, Experience
import pycountry
from PIL import Image
import io
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from users.serializers.user_profile_serializers import (
    UserProfileCreateUpdateSerializer,
    UserProfileSerializer,
    ReviewSerializer,
    EducationSerializer,
    CareerSerializer,
    ExperienceSerializer
)

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_validate_username_unique(self):
        """Ensure validate_username raises an error if username already exists."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_username('existinguser')

    def test_validate_username_unique_new(self):
        """Ensure validate_username allows a new unique username."""
        serializer = UserSerializer()
        self.assertEqual(serializer.validate_username('newuser'), 'newuser')

    def test_validate_email_unique(self):
        """Ensure validate_email raises an error if email already exists."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_email('existinguser@example.com')

    def test_validation_email_unique_new(self):
        """Ensure validation_email allows a new unique email."""
        serializer = UserSerializer()
        self.assertEqual(serializer.validate_email('new@example.com'), 'new@example.com')

    def test_validate_name_fields(self):
        """Ensure validate_name_fields raises an error if first_name or last_name is empty."""
        serializer = UserSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_name_fields({'first_name':'', 'last_name':'Doe'})
        with self.assertRaises(ValidationError):
            serializer.validate_name_fields({'first_name':'John', 'last_name':''})

    def test_validate_name_fields_valid(self):
        """Ensure validation_name_fields allows non-empty names."""
        serializer = UserSerializer()
        data = {'first_name':'John', 'last_name':'Doe'}
        self.assertEqual(serializer.validate_name_fields(data), data)

    def test_update_user(self):
        """Ensure update_user correctly updates user attributes."""
        serializer = UserSerializer()
        updated_data = {'first_name':'Jane', 'last_name':'Smith'}
        updated_user = serializer.update_user(self.user, updated_data)
        self.assertEqual(updated_user.first_name, 'Jane')
        self.assertEqual(updated_user.last_name, 'Smith')

    def test_delete_user(self):
        """Ensure delete_user removes the user from the database."""
        serializer = UserSerializer()
        response = serializer.delete_user(self.user)
        self.assertEqual(response, {'message':'User account deleted successfully.'})
        self.assertFalse(User.objects.filter(id=self.user.id).exists())


class UserProfileCreateUpdateSerializerTest(TestCase):
    def setUp(self):
        self.serializer = UserProfileCreateUpdateSerializer()
        self.valid_image = self.create_test_image("JPEG", (500,500))
        self.large_image = self.create_test_image("JPEG", (5000,5000))
        self.invalid_format_image = self.create_test_image("PDF", (600,600))
        
    def create_test_image(self, format='JPEG', size=(100,100),color=(255,0,0), file_size=None):
        """Generates an in-memory image file for testing."""
        image = Image.new("RGB", size, color)
        img_io = io.BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(f"test_image.{format.lower()}",
                                  img_io.getvalue(),
                                  content_type=f"image/{format.lower()}")

    def test_validate_country_valid(self):
        """Ensure validate_country accepts a valid country name."""
        self.assertEqual(self.serializer.validate_country("France"), "France")

    def test_validate_country_too_short(self):
        """Ensure validate_country raises an error if the country name is too short."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_country('F')

    def test_validate_country_invalid(self):
        """Ensure validate_country raises an error if the country name is invalid."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_country("Lalaland")

    def test_validate_profile_picture_upload(self):
        """Ensure validate_profile_picture field allows file uploads."""
        self.assertEqual(self.serializer.validate_profile_picture(self.valid_image), self.valid_image)
        
    def test_validate_profile_picture_too_large(self):
        """Ensure validate_profile_picture rejects images that exceeds dimension limits."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.large_image)

    def test_validate_profile_picture_invalid_format(self):
        """Ensure validate_profile_picture rejects images with an invalid format."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.invalid_format_image)


class UserProfileSerializerTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.profile1 = UserProfile.objects.create(
            user=self.user1,
            country='USA',
            job_title='Developer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123',
            first_name='Test2',
            last_name='User',
        )
        self.profile2 = UserProfile.objects.create(
            user=self.user2,
            country='USA',
            job_title='Developer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.serializer = UserProfileSerializer(self.profile2)
    
    

    def test_get_average_rating_with_reviews(self):
        """Test that the average rating is calculated correctly when reviews exist."""
        review1 = Review.objects.create(
            user_profile=self.profile2,
            reviewer=self.user1,
            comment='Great profile!',
            rating=5,
        )
        review2 = Review.objects.create(
            user_profile=self.profile2,
            reviewer=self.user1,
            comment='Great profile!',
            rating=4,
        )
        self.assertEqual(self.serializer.data['average_rating'], 4.5)

    def test_get_average_rating_no_review(self):
        """Test that the average rating is 0 when no reviews exist."""
        self.assertEqual(self.serializer.data['average_rating'], 0.0)


class ReviewSerializerTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.profile1 = UserProfile.objects.create(
            user=self.user1,
            country='USA',
            job_title='Developer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123',
            first_name='Test2',
            last_name='User',
        )
        self.profile2 = UserProfile.objects.create(
            user=self.user2,
            country='USA',
            job_title='Developer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.review_data = {
            'user_profile':self.profile2,
            'reviewer':self.user1.id,
            'rating':8,
            'comment':'Great service!',
        }

    def test_valid_review_serializer(self):
        """Test that a valid review is serialized correctly."""
        serializer = ReviewSerializer()
        valid_ratings = [0, 5, 10]
        for rating in valid_ratings:
            try:
                result = serializer.validate_rating(rating)
                self.assertEqual(result, rating, f"Rating {rating} should be valid.")
            except serializers.ValidationError:
                self.fail(f"Rating {rating} should not raise a ValidationError.")

    def test_validate_rating_invalid(self):
        """Test that invalid ratings raise a ValidationError."""
        invalid_ratings = [-1, 11, -10, 100]
        with self.assertRaises(ValidationError):
            serializer = ReviewSerializer(data={'rating':invalid_ratings})
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_valid_data(self):
        """Test creating a serializer with a valid review data."""
        serializer = ReviewSerializer(data=self.review_data)
        self.assertTrue(serializer.is_valid(),
                        f"Serializer errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['rating'], 8)
        self.assertEqual(serializer.validated_data['comment'], 'Great service!')
        self.assertEqual(serializer.validated_data['reviewer'], self.user1)

    def test_serializer_read_only_fields(self):
        """Verify that read-only fields cannot be modified."""
        data={
            'user_profile':self.profile2,
            'reviewer':self.user1.id,
            'rating':8,
            'comment':'Great service!',
        }
        serializer = ReviewSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(serializer.errors)
        validated_data = serializer.validated_data
        self.assertNotIn('id', validated_data)
        self.assertNotIn('reviewer_info', validated_data)

    def test_serializer_missing_fields(self):
        """Test serializer behavior with missing required fields."""
        incomplete_data = {
            'user_profile':self.profile2,
            'reviewer':self.user1.id,
            'rating':8,
        }
        serializer = ReviewSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('comment', serializer.errors)

    def test_reviewer_info_population(self):
        """Verify that reviewer_info is populated correctly."""
        review = Review.objects.create(
            user_profile = self.profile2,
            reviewer = self.user1,
            rating = 8,
            comment = 'Great service!'
        )
        serializer = ReviewSerializer(review)
        self.assertIn('reviewer_info', serializer.data)
        self.assertEqual(serializer.data['reviewer_info']['username'],self.user1.username)

    def test_rating_type_validation(self):
        """Ensure rating only accepts numeric types."""
        with self.assertRaises(ValidationError):
            serializer = ReviewSerializer(data={
                'user_profile':self.profile2,
                'reviewer':self.user1.id,
                'rating':'invalid_rating',
                'comment':'Great service!',
            })
            serializer.is_valid(raise_exception=True)


class EducationSerializerTest(TestCase):
    def setUp(self):
        
        self.serializer = UserProfileCreateUpdateSerializer()
        self.valid_image = self.create_test_image("JPEG", (500,500))
        self.large_image = self.create_test_image("JPEG", (5000,5000))
        self.invalid_format_image = self.create_test_image("PDF", (600,600))
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
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.education_data = {
            'user_profile': self.profile,
            'school_name':"University",
            'diploma':'Bachelor',
            'description':'Bachelor at University',
            'picture': self.valid_image,
        }
        
    def create_test_image(self, format='JPEG', size=(100,100),color=(255,0,0), file_size=None):
        """Generates an in-memory image file for testing."""
        image = Image.new("RGB", size, color)
        img_io = io.BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(f"test_image.{format.lower()}",
                                  img_io.getvalue(),
                                  content_type=f"image/{format.lower()}")
    
    def test_validate_profile_picture_upload(self):
        """Ensure validate_profile_picture field allows file uploads."""
        self.assertEqual(self.serializer.validate_profile_picture(self.valid_image), self.valid_image)
        
    def test_validate_profile_picture_too_large(self):
        """Ensure validate_profile_picture rejects images that exceeds dimension limits."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.large_image)

    def test_validate_profile_picture_invalid_format(self):
        """Ensure validate_profile_picture rejects images with an invalid format."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.invalid_format_image)
    
    def test_missing_picture(self):
        """Test that missing picture field does not raise validation error."""
        missing_picture = {
            'user_profile': self.profile.id,
            'school_name':"University",
            'diploma':'Bachelor',
            'description':'Bachelor at University',
            'picture': None,
        }
        serializer = EducationSerializer(data=missing_picture)  
        self.assertTrue(serializer.is_valid(), "Serializer should be valid with None picture")
        self.assertIsNone(serializer.validated_data['picture'])

    def test_valid_picture_with_optional_field(self):
        """Test that picture field can be omitted without issues."""
        missing_picture = {
            'user_profile': self.profile.id,
            'school_name':"University",
            'diploma':'Bachelor',
            'description':'Bachelor at University', 
        }
        serializer = EducationSerializer(data=missing_picture)
        self.assertTrue(serializer.is_valid(), "Serializer should be valid without picture")
        self.assertNotIn('picture', serializer.validated_data)

    
class CareerSerializerTest(TestCase):
    def setUp(self): 
        self.serializer = UserProfileCreateUpdateSerializer()
        self.valid_image = self.create_test_image("JPEG", (500,500))
        self.large_image = self.create_test_image("JPEG", (5000,5000))
        self.invalid_format_image = self.create_test_image("PDF", (600,600))
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
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.career_data = {
            'user_profile': self.profile,
            'job_title':"Designer",
            'company_name':'Apple',
            'job_status':'full-time',
            'picture': self.valid_image,
        }
        
    def create_test_image(self, format='JPEG', size=(100,100),color=(255,0,0), file_size=None):
        """Generates an in-memory image file for testing."""
        image = Image.new("RGB", size, color)
        img_io = io.BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(f"test_image.{format.lower()}",
                                  img_io.getvalue(),
                                  content_type=f"image/{format.lower()}")
    
    def test_validate_profile_picture_upload(self):
        """Ensure validate_profile_picture field allows file uploads."""
        self.assertEqual(self.serializer.validate_profile_picture(self.valid_image), self.valid_image)
        
    def test_validate_profile_picture_too_large(self):
        """Ensure validate_profile_picture rejects images that exceeds dimension limits."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.large_image)

    def test_validate_profile_picture_invalid_format(self):
        """Ensure validate_profile_picture rejects images with an invalid format."""
        with self.assertRaises(ValidationError):
            self.serializer.validate_profile_picture(self.invalid_format_image)

    def test_invalid_job_status(self):
        """Test that an invalid job status raises a validation error."""
        invalid_data = self.career_data.copy()
        invalid_data['job_status'] = 'invalid_status'
        serializer = CareerSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("job_status", serializer.errors)

    def test_valid_job_status(self):
        """Test that an valid job status passes validation."""
        valid_data = self.career_data.copy()
        valid_data['job_status'] = 'part-time'
        serializer = CareerSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertIn("job_status", 'part-time')


class ExperienceSerializerTest(TestCase):
    def setUp(self):
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
            rating='0',
            description="Experience software engineer specializing in Django."
        )
        self.experience_data = {
            'user_profile': self.profile,
            'name': 'Experience',
            'weight': 1
        }
    
    def test_valid_serializer(self):
        """Test that a valid serializer instance is created successfully."""
        serializer = ExperienceSerializer(data=self.experience_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_weight(self):
        """Test that an invalid weight value raises a validation error."""
        invalid_data = self.experience_data.copy()
        invalid_data['weight'] = 'invalid_weight'

        serializer = ExperienceSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)

    def test_valid_weight(self):
        """Test that an valid weight value passes validation."""
        valid_data = self.experience_data.copy()
        valid_data['weight'] = 2

        serializer = ExperienceSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertIn('weight', serializer.validated_data)
        self.assertEqual(serializer.validated_data['weight'], 2)

    def test_missing_weight(self):
        """Test that missing weight field raises a validation error."""
        data_mising = {
            'user_profile': self.profile,
            'name': 'Experience',
        }
        serializer = ExperienceSerializer(data=data_mising)
        self.assertFalse(serializer.is_valid())
        self.assertIn("weight", serializer.errors)

    def test_weight_display(self):
        """Test that weight_display returns the correct human-readable value."""
        experience = Experience.objects.create(
            user_profile = self.profile,
            name = 'Designer',
            weight = 3
        )
        serializer = ExperienceSerializer(instance=experience)
        expected_display = experience.get_weight_display()
        self.assertEqual(serializer.data['weight_display'], expected_display)



  
    