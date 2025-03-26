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

from users.models.settings_models import (
    Settings,
    NotificationPreferences,
    PaymentSettings,
    SupportTicket
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


class SettingsModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )

    def test_settings_creation(self):
        """Test if the settings instance is created succcesfully."""
        settings = Settings.objects.create(user=self.user)
        self.assertEqual(settings.user.username, 'testuser')

    def test_settings_update(self):
        settings = Settings.objects.create(user=self.user)
        settings.profile = {'theme':'dark'}
        settings.save()
        updated_settings = Settings.objects.get(user=self.user)
        self.assertEqual(updated_settings.profile, {'theme':'dark'})

    def test_settings_str(self):
        """Test if the string representtion of the settings is correct."""
        settings = Settings.objects.create(user=self.user)
        self.assertEqual(str(settings), 'Settings for testuser')
        

class NotificationPreferencesModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.notification_preferences = NotificationPreferences.objects.create(user=self.user)

    def test_notification_preferences_creation(self):
        """Test if the notification preferences instance is created successfully."""
        self.assertEqual(self.notification_preferences.user.username, 'testuser')
        self.assertTrue(self.notification_preferences.booking_notifications)

    def test_notification_preferences_update(self):
        """Test updating notification preferences for a user."""
        self.notification_preferences.booking_notifications = False
        self.notification_preferences.save()
        updated_preferences = NotificationPreferences.objects.get(user=self.user)
        self.assertFalse(updated_preferences.booking_notifications)

    def test_notification_preferences_str(self):
        """Test if the string representation of the notification preferences is correct."""
        self.assertEqual(str(self.notification_preferences), "Notification preferences for testuser")



class PaymentSettingsModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.payment_settings = PaymentSettings.objects.create(user=self.user)

    def test_payment_settings_creation(self):
        """Test if the payment settings instance is created successfully."""
        self.assertEqual(self.payment_settings.user.username, 'testuser')
        self.assertEqual(self.payment_settings.payment_method, 'bank_transfer')

    def test_payment_settings_update(self):
        """Test updating payment settings for a user."""
        self.payment_settings.payment_method = 'paypal'
        self.payment_settings.save()
        updated_payment_settings = PaymentSettings.objects.get(user=self.user)
        self.assertEqual(updated_payment_settings.payment_method, 'paypal')

    def test_payment_settings_str(self):
        """Test if the string representation of payment settings is correct."""
        self.assertEqual(str(self.payment_settings), "Payment settings for testuser")


class SupportTicketModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.support_ticket= SupportTicket.objects.create(
            user=self.user,
            issue_type = 'account',
            description = 'Test account issue'
            )

    def test_support_ticket_creation(self):
        """Test if the support ticket instance is created successfully."""
        self.assertEqual(self.support_ticket.user.username, 'testuser')
        self.assertEqual(self.support_ticket.issue_type, 'account')

    def test_support_ticket_resolution(self):
        """Test resolving a support ticket"""
        self.support_ticket.resolved = True
        self.support_ticket.resolution_notes = 'Issue resolved'
        self.support_ticket.save()
        updated_ticket = SupportTicket.objects.get(user=self.user)
        self.assertTrue(updated_ticket.resolved)
        self.assertEqual(updated_ticket.resolution_notes, 'Issue resolved')

    def test_support_ticket_str(self):
        """Test if the string representation of support ticket is correct."""
        self.assertEqual(str(self.support_ticket), 'Support ticket (account) for testuser')