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
        user_id (OneToOneField): A one-to-one relationship with the User model.
        role (CharField): The user's role.
        company (CharField): The company the user works for.
        description (TextField): A brief description of the user.
        profile_picture (CharField): URL or path to the user's profile picture.
        total_meetings (IntegerField): The number of meetings the user has attended.
        rating (DecimalField): The user's average rating, with two decimal places.

        career_title (CharField): Job title in the user's career.
        career_location (CharField): Job location for the user's career.
        career_status (CharField): Employment status of the user (either part-time or full-time).
        career_description (CharField): Detailed description of the user's career.
        career_picture (CharField): URL or path to a picture representing the user's career.

        education_location (CharField): Location of the user's education.
        education_diploma (CharField): Type of diploma the user has earned.
        education_description (TextField): Detailed description of the user's education.
        education_picture (CharField): URL or path to a picture representing the user's education.
        experience_id (ForeignKey): Link to the Experience model, containing the user's work experience.
    
    Methods:
        __str__: Returns a string representation of the user profile.
    """


    user_id = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_profile")
    role = models.ForeignKey("Role", on_delete=models.CASCADE, related_name="user_profiles")
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="user_profiles")
    description = models.TextField(max_length=500, null=True)
    profile_picture = models.CharField(max_length=64, null=True)
    total_meetings = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, default=0.0)

    # Career info
    career_title = models.CharField(max_length=64, null=True)
    career_location = models.CharField(max_length=64, null=True)
    career_status = models.CharField(max_length=50, choices= [("part-time", "Part-time"), ("full-time", "Full-time")], null=True)
    career_description = models.CharField(max_length=64, null=True)
    career_picture = models.CharField(max_length=64, null=True)

    # Education info
    education_location = models.CharField(max_length=64, null=True)
    education_diploma = models.CharField(max_length=64, null=True)
    education_description = models.TextField(max_length=500, null=True)
    education_picture = models.CharField(max_length=64, null=True)

    experience_id = models.ForeignKey("Experience", on_delete=models.SET_NULL, null=True, related_name="user_experiences")

    def __str__(self):
        return f"Profile of {self.user.username}"
    



class Experience(models.Model):
    """
    Experience model representing the user's work or professional experiences.

    Attributes:
        id (UUIDField): Unique identifier for each experience entry.
        name (CharField): Name of the experience.
        weight (IntegerField): A numeric value representing the importance or level of the experience.
    
    Methods:
        __str__: Returns the name of the experience for string representation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False)
    weight = models.IntegerField()

    def __str__(self):
        return self.name
    

class Role(models.Model):
    """
    Represents a role that can be associated with a listing.

    Attributes:
        name (str): The name of the role.

    Methods:
        __str__: Returns a human-readable string representation of the role name.
    """
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class Company(models.Model):
    """
    Represents a company that can be associated with a listing.

    Attributes:
        name (str): The name of the company.
        description (str): A brief description of the company.

    Methods:
        __str__: Returns a human-readable string representation of the company name.
    """
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=1000, null=True)

    def __str__(self):
        return self.name



