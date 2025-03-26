from django.test import TestCase
from django.db.models.signals import post_save, post_delete
from django.db import models
from users.models.profile_models import Review, UserProfile
from users.models.user_models import User
from django.db.models import Avg

class ReviewSignalTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.user_profile1 = UserProfile.objects.create(user=self.user1, country='USA', job_title='Developer')
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.user_profile2 = UserProfile.objects.create(user=self.user2, country='USA', job_title='Developer')
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
        )
        self.user_profile3 = UserProfile.objects.create(user=self.user3, country='USA', job_title='Developer')
        self.review1 = Review.objects.create(
            user_profile=self.user_profile2,
            reviewer=self.user1,
            comment='Great profile!',
            rating=4,
        )
        self.review2= Review.objects.create(
            user_profile=self.user_profile2,
            reviewer=self.user3,
            comment='Great profile!',
            rating=5,
        )

    def test_update_profile_rating_on_review_success(self):
        """Test that the profile rating is updated when a review is saved."""
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 4.5)
        review3= Review.objects.create(
            user_profile=self.user_profile2,
            reviewer=self.user3,
            comment='Great profile!',
            rating=3,
        )
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 4.0)


    def test_update_profile_rating_on_review_delete(self):
        """Test that the profile rating is updated when a review is deleted."""
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 4.5)
        self.review1.delete()
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 5.0)

    def test_review_update_rating(self):
        """Test that updating a review triggers the rating update."""
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 4.5)
        self.review1.rating = 3
        self.review1.save()
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 4.0)

    def test_review_deletion_zero_rating(self):
        """Test that deleting all reviews results in the profile rating being 0."""
        self.review1.delete()
        self.review2.delete()
        self.user_profile2.refresh_from_db()
        self.assertEqual(self.user_profile2.rating, 0.0)

