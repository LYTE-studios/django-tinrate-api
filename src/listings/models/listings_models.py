import uuid
from django.utils.timezone import now
from django.db import models
from django.conf import settings
from users.models.user_models import User
from users.models.profile_models import UserProfile, Experience, Role, Company

class Listing(models.Model):
    """
    Represents a listing posted by a user.

    Attributes:
        id (UUID): Unique identifier for the listing.
        user (User): The user who created the listing (ForeignKey to User).
        role (Role): The role associated with the listing (ForeignKey to Role).
        company (Company): The company associated with the listing (ForeignKey to Company).
        title (str): The title of the listing (e.g., job title or service name).
        description (UserProfile): A description of the listing, typically taken from the user's profile (ForeignKey to UserProfile).
        amount (Decimal): The amount or price associated with the listing.
        experience (Experience): The experience required for the listing (ForeignKey to Experience).
        availability (DateTime): The availability date and time for the listing.
        created_at (DateTime): Timestamp of when the listing was created.

    Methods:
        __str__: Returns a human-readable string representation of the listing, including the title, role, and company.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="listings", default="")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="listings", null=True, blank=True)
    title = models.CharField(max_length=255, null=True)
    description = models.TextField(max_length=1000, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="listings", default="")
    availability = models.DateTimeField(default=now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.role.name} - {self.company.name})"
