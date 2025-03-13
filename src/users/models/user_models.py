import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=64, null=True)
    last_name = models.CharField(max_length=64, null=True)
    username = models.CharField(max_length=64, null=True, unique=True)
    email = models.CharField(max_length=64, null=False)

    is_customer = models.BooleanField(default=True)
    is_expert = models.BooleanField(default=False)
    allow_cancellation_fee = models.BooleanField(default=False)

    def __str__(self):
        return self.username