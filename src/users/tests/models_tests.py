import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models.user_models import User
from django.contrib.auth import get_user_model
from users.models.profile_models import (
    UserProfile,
    Experience,
    Career,
    Education,
    Review
)

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='John',
            last_name='Doe',
            username='johndoe',
            email='johndoe@example.com'
        )

    def test_user_creation(self):
        """Test that a user is correctly created."""
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.username, 'johndoe')
        self.assertEqual(self.user.email, 'johndoe@example.com')
        self.assertIsInstance(self.user.id, uuid.UUID)

    def test_username_uniqueness(self):
        """Test that the username field is unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                first_name='Jane',
                last_name='Doe',
                username='johndoe',
                email='janedoe@example.com'
            )

    def test_email_uniqueness(self):
        """Test that the email field is unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                first_name='Jane',
                last_name='Doe',
                username='janedoe',
                email='johndoe@example.com',
            )

    def test_str_method(self):
        """Test the string representation of the user model."""
        self.assertEqual(str(self.user), 'johndoe')


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='John',
            last_name='Doe',
            username='johndoe',
            email='johndoe@example.com'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            country='USA',
            job_title='Software Engineer',
            company_name='TechCorp',
            total_meetings=5,
            meetings_completed=4,
            total_minutes=300,
            rating=4.5,
            description="Experience software engineer specializing in Django."
        )

    def test_profile_creation(self):
        """Test that a user profile is correctly createed and linked to a user."""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.country, 'USA')
        self.assertEqual(self.profile.job_title, 'Software Engineer')
        self.assertEqual(self.profile.company_name, 'TechCorp')
        self.assertEqual(self.profile.total_meetings, 5)
        self.assertEqual(self.profile.meetings_completed, 4)
        self.assertEqual(self.profile.rating, 4.5)

    def test_str_method(self):
        """Test the string representation of the user profile model."""
        self.assertEqual(str(self.profile), 'Profile of John Doe.')

    def test_default_value(self):
        """Test that default values for numerical fields are correctly set."""
        new_user = User.objects.create_user(
            first_name='Jane',
            last_name='Doe',
            username='janedoe',
            email='janedoe@example.com',
        )
        new_profile = UserProfile.objects.create(
            user=new_user,
            country='Canada',
            job_title='Designer',
            company_name='Designer&Co'
        )
        self.assertEqual(new_profile.total_meetings, 0)
        self.assertEqual(new_profile.meetings_completed, 0)
        self.assertEqual(new_profile.total_minutes, 0)
        self.assertEqual(new_profile.rating, 0.0)


class ExperienceModelTest(TestCase):
    def setUp(self):
        user_profile = UserProfile.objects.create(user=get_user_model().objects.create_user('testuser', 'testpassword'))
        self.experience = Experience.objects.create(user_profile=user_profile, name='Python', weight=Experience.high)

    def test_experience_creation(self):
        """Test if the experience instance is created successfully."""
        self.assertEqual(self.experience.name, 'Python')
        self.assertEqual(self.experience.weight, Experience.high)

    def test_experience_str(self):
        """Test if the string representation of the experience is correct."""
        self.assertEqual(str(self.experience), 'Python')


class CareerModelTest(TestCase):
    def setUp(self):
        user_profile = UserProfile.objects.create(user=get_user_model().objects.create_user('testuser', 'testpassword'))
        self.career = Career.objects.create(
            user_profile=user_profile,
            job_title='Designer', 
            company_name='Design&Co',
            job_status='full-time',
            description='Software development role'   
            )
        
    def test_career_creation(self):
        """Test if the career instance is created successfully."""
        self.assertEqual(self.career.job_title, 'Designer')
        self.assertEqual(self.career.company_name, 'Design&Co')

    def test_career_str(self):
        """Test if the string representation of the career is correct."""
        self.assertEqual(str(self.career), 'Designer at Design&Co')


class EducationModelTest(TestCase):
    def setUp(self):
        user_profile=UserProfile.objects.create(user=get_user_model().objects.create_user('testuser', 'testpassword'))
        self.education = Education.objects.create(
            user_profile=user_profile,
            school_name='University',
            diploma='Degree',
            description="Bachelor's degree in computer science"
        )
    
    def test_education_creation(self):
        """Test if the education instance is created successfully."""
        self.assertEqual(self.education.school_name, 'University')
        self.assertEqual(self.education.diploma, 'Degree')

    def test_education_str(self):
        """Test if the string representation of the education is correct."""
        self.assertEqual(str(self.education), 'Degree from University')

class ReviewModelTest(TestCase):
    def setUp(self):
        reviewer = get_user_model().objects.create_user('reviewer', 'password')
        user_profile = UserProfile.objects.create(user=get_user_model().objects.create_user('testuser', 'testpassword'))
        self.review = Review.objects.create(
            reviewer=reviewer,
            user_profile=user_profile,
            rating= 4.5,
            comment='Good meeting!'
        )
    
    def test_review_creation(self):
        """Test if the review instance is created successfully."""
        self.assertAlmostEqual(self.review.rating, 4.5)
        self.assertEqual(self.review.comment, 'Good meeting!')

    def test_review_str(self):
        """Test if the string representation of the review is correct."""
        self.assertEqual(str(self.review), 'Review by reviewer for testuser')