import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model that extends the built-in AbstractUser with additional fields.

    Attributes:
        id (UUIDField): Unique identifier for the user, automatically generated.
        first_name (CharField): First name of the user.
        last_name (CharField): Last name of the user.
        username (CharField): Unique username for the user.
        email (CharField): Unique email address of the user.
        allow_cancellation_fee (BooleanField): Flag indicating whether the user allows cancellation fees.
    
    Methods:
        __str__: Returns the username of the user for string representation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=64, null=True)
    last_name = models.CharField(max_length=64, null=True)
    username = models.CharField(max_length=64, null=True, unique=True)
    email = models.CharField(max_length=64, null=False, unique=True)
    allow_cancellation_fee = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = "users"
    

