from django.db import models
from users.models import User

class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes") 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
