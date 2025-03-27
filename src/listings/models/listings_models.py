from django.db import models
from django.conf import settings
from users.models.profile_models import UserProfile, Experience
from users.models.settings_models import PaymentSettings


    
class Day(models.Model):
    """
    Represents a day of the week and its availability status.

    Attributes:
        day_of_week (CharField): The name of the day (Monday-Sunday).
        is_available (BooleanField): Indicates if the expert is available on this day.
        start_time (TimeField): The available start time (optional).
        end_time (TimeField): The available end time (optional).
    """

    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    day_of_week = models.CharField(choices=DAY_CHOICES, max_length=9)
    is_available = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.day_of_week.capitalize()
    


class Availability(models.Model):
    """
    Represents an expert's weekly availability, linking to specific days.

    Attributes:
        listing (ForeignKey): The listing that this availability applies to.
        monday-sunday (ForeignKey): Links each day of the week to a `Day` instance.
    """

    monday = models.ForeignKey(Day, related_name="monday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    tuesday = models.ForeignKey(Day, related_name="tuesday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    wednesday = models.ForeignKey(Day, related_name="wednesday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    thursday = models.ForeignKey(Day, related_name="thursday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    friday = models.ForeignKey(Day, related_name="friday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    saturday = models.ForeignKey(Day, related_name="saturday_availability", on_delete=models.SET_NULL, null=True, blank=True)
    sunday = models.ForeignKey(Day, related_name="sunday_availability", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Availability for {self.listing.user_profile.user.first_name} {self.listing.user_profile.user.last_name}" 

class Listing(models.Model):
    """
    Represents a service listing created by a user.

    Attributes:
        user_profile (ForeignKey): Links the listing to the user's profile.
        experience (ForeignKey): Links the listing to a relevant experience.
        pricing_per_hour (DecimalField): The hourly price for the service.
        service_description (TextField): A description of the service offered.
        availability (OneToOneField): The availability related to the listing.
        completion_status (BooleanField): Indicates whether the listing is active or completed.
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, null=True)

    pricing_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    service_description = models.TextField(max_length=500, null=True, blank=True)
    availability = models.OneToOneField(Availability, on_delete=models.CASCADE)
    completion_status = models.BooleanField(default=False)

    def __str__(self):
        return f"Listing by {self.user_profile.user.first_name} {self.user_profile.user.last_name}"


class Meeting(models.Model):
    """
    Represents a scheduled meeting between a user and an expert.

    Attributes:
        listing (ForeignKey): The listing that the meeting is for.
        user (ForeignKey): The user who booked the meeting.
        availability (ForeignKey): The specific availability slot for the meeting.
        payment (ForeignKey): The payment details associated with the meeting.
        duration (PositiveIntegerField): The length of the meeting (30, 60, or 90 minutes).
    """
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE,related_name='meetings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meetings')
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE, related_name='meetings')
    payment = models.ForeignKey(PaymentSettings, on_delete=models.SET_NULL, null=True, blank=True)

    DURATION_CHOICES = [
        (30, '30 minutes'),        
        (60, '1 hour'),        
        (90, '1.5 hours'),        
    ]
    duration = models.PositiveIntegerField(choices=DURATION_CHOICES)

    def __str__(self):
        return f"Meeting: {self.user.first_name} with {self.listing.user_profile.user.first_name} ({self.duration} min)"

