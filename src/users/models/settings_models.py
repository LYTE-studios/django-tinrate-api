import uuid
from django.db import models
from .user_models import User
from django.conf import settings
from django.utils.timezone import now



class Settings(models.Model):
    """
    Represents a user's settings in the system.
    
    Attributes:
        user (User): The user to whom the settings belong.
        profile (JSON): The user's profile settings stored as JSON data.
        account_security (JSON): The user's account security settings stored as JSON data.
        notification_pref (JSON): The user's notification preferences stored as JSON data.
        payment_settings (JSON): The user's payment settings stored as JSON data.
        support_help (JSON): The user's support help information stored as JSON data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings")
    profile = models.JSONField(null=True, blank=True)
    account_security = models.JSONField(null=True, blank=True)
    notification_pref = models.JSONField(null=True, blank=True)
    payment_settings = models.JSONField(null=True, blank=True)
    support_help = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Settings for {self.user.username}"
    
    class Meta:
        db_table = "user_settings"
        verbose_name = "User Setting"
        verbose_name_plural = "User Settings"