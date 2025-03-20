import uuid
from django.db import models
from .user_models import User
from django.conf import settings
from django.utils.timezone import now



class UserProfile(models.Model):
    """
    Profile model that stores additional information about a user.

    This model contains detailed information about the user's career, education, 
    profile picture, meetings, and rating. It is linked to a User via a OneToOneField.

    Attributes:
        user (OneToOneField): A one-to-one relationship with the User model.
        profile_picture (ImageField): URL or path to the user's profile picture.
        country (CharField): The user's country.
        job_title (CharField): The user's job title.
        company_name (CharField): The company the user works for.
        total_meetings (IntegerField): The total number of meetings attended by the user.
        meetings_completed (IntegerField): The total number of meetings the user has completed.
        total_minutes (IntegerField): The total minutes spent in meetings by the user.
        rating (DecimalField): The average rating of the user, calculated from reviews.
        description (TextField): A brief description about the user.
        
    Methods:
        __str__: Returns a string representation of the user profile in the format "Profile of {first_name} {last_name}".
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_profile")

    # Profile Info
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    country = models.CharField(max_length=64)
    job_title = models.CharField(max_length=64)
    company_name = models.CharField(max_length=64, null=False)

    # Statistics
    total_meetings = models.IntegerField(default=0)
    meetings_completed = models.IntegerField(default=0)
    total_minutes = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)

    #Overview Section
    description = models.TextField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.first_name} {self.user.last_name}."
    

class Experience(models.Model):
    """
    Experience model representing the user's work or professional experiences.

    Attributes:
        user_profile (ForeignKey): Link to the UserProfile model.
        name (CharField): Name of the experience (e.g., a tool or a skill).
        weight (IntegerField): A numeric value representing the importance or level of the experience (choices: low, medium, high).

    Methods:
        __str__: Returns the name of the experience for string representation.
    """

    low = 1
    medium = 2
    high = 3

    weight_choices = [
        (low, 'low'),
        (medium, 'medium'),
        (high, 'high'),
    ]
    user_profile = models.ForeignKey(UserProfile, related_name="experiences", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=64, null=False)
    weight = models.IntegerField(choices=weight_choices)

    def __str__(self):
        return self.name
    

class Career(models.Model):
    """
    Represents a user's career role and associated details.

    Attributes:
        user_profile (ForeignKey): Link to the UserProfile model.
        job_title (CharField): The user's job title.
        company_name (CharField): The company the user works for.
        job_status (CharField): Employment status (e.g., 'full-time', 'part-time').
        description (TextField): Detailed description of the user's role.
        picture (ImageField): Picture related to the user's career (e.g., company logo or workspace).
        
    Methods:
        __str__: Returns a human-readable string representation of the job title and company name.
    """
    user_profile = models.ForeignKey(UserProfile, related_name='careers', on_delete=models.CASCADE)
    job_title = models.CharField(max_length=64, null=False)
    company_name = models.CharField(max_length=64, null=False)
    job_status = models.CharField(max_length=64, choices=[
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time')
    ])
    description = models.TextField(max_length=500)
    picture = models.ImageField(upload_to='career_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class Education(models.Model):
    """
    Represents a user's education and related details.

    Attributes:
        user_profile (ForeignKey): Link to the UserProfile model.
        school_name (CharField): The name of the school or university.
        diploma (CharField): The diploma or degree the user has earned.
        description (TextField): Detailed description of the user's education.
        picture (ImageField): Picture related to the user's education (e.g., school logo or graduation photo).
        
    Methods:
        __str__: Returns a human-readable string representation of the diploma and school name.
    """
    user_profile = models.ForeignKey(UserProfile, related_name='educations', on_delete=models.CASCADE, null=True, blank=True)
    school_name = models.CharField(max_length=64)
    diploma = models.CharField(max_length=64)
    description = models.TextField(max_length=500)
    picture = models.ImageField(upload_to='education_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.diploma} from {self.school_name}"

class Review(models.Model):
    """
    Represents a review left by a user for another user, including rating and comments.

    Attributes:
        user_profile (ForeignKey): Link to the UserProfile being reviewed.
        reviewer (ForeignKey): Link to the user who gave the review.
        rating (DecimalField): The rating given by the reviewer (maximum 10 with two decimal places).
        comment (TextField): The comment left by the reviewer.
        
    Methods:
        __str__: Returns a human-readable string representation of the review.
    """
    user_profile = models.ForeignKey(UserProfile, related_name='reviews', on_delete=models.CASCADE, null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='given_reviews', on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    comment = models.TextField(max_length=500)

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.user_profile.user.username}"

