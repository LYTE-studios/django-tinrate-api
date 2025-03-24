import uuid
from django.db import models
from users.models.user_models import User
from django.conf import settings
from django.utils.timezone import now



class Settings(models.Model):
    """
    Stores a user's various settings as JSON fields.
    
    This model allows dynamic storage of different settings categories,
    making it easier to expand or modify settings without altering the database schema.
    
    Attributes:
        user (User): The user to whom the settings belong (One-to-One relationship).
        profile (JSONField): Stores profile-related settings, such as display preferences.
        account_security (JSONField): Stores security-related settings, such as two-factor authentication preferences.
        notification_pref (JSONField): Stores the user's notification preferences.
        payment_settings (JSONField): Stores payment-related settings.
        support_help (JSONField): Stores support and help-related settings or preferences.
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


class NotificationPreferences(models.Model):
    """
    Stores user preferences for different types of notifications.
    
    This model allows users to customize which notifications they receive and their preferred method of communication.
    
    Attributes:
        user (User): The user associated with these preferences (One-to-One relationship).
        booking_notifications (bool): Whether the user wants to receive booking-related notifications.
        payments_notifications (bool): Whether the user wants to receive payment-related notifications.
        meeting_reminders (bool): Whether the user wants to receive reminders for upcoming meetings.
        updates_promotions (bool): Whether the user wants to receive platform updates and promotional content.
        preferred_method (str): The preferred method of receiving notifications (email, SMS, push, etc.).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications_preferences")

    # Notification toggles
    booking_notifications = models.BooleanField(default=True)
    payments_notifications = models.BooleanField(default=True)
    meeting_reminders = models.BooleanField(default=True)
    updates_promotions = models.BooleanField(default=True)
    
    NOTIFICATION_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('all', 'All Methods'),
    ]
    preferred_method = models.CharField(max_length=10, choices=NOTIFICATION_METHODS)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    

class PaymentSettings(models.Model):
    """
    Stores user payment settings and preferences.
    
    This model handles payment methods, linked accounts, and optional cancellation fee preferences.
    
    Attributes:
        user (User): The user associated with these payment settings (One-to-One relationship).
        payment_method (str): The preferred payment method (e.g., PayPal, bank transfer, cryptocurrency).
        allow_cancellation_fee (bool): Whether the user allows cancellation fees to be deducted.
        paypal_email (str): Email address linked to the user's PayPal account (optional).
        bank_account_name (str): Name of the bank account holder (optional).
        bank_account_number (str): Bank account number (optional).
        bank_name (str): Name of the bank (optional).
        crypto_wallet_address (str): Wallet address for cryptocurrency transactions (optional).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_settings")

    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'Paypal'),
        ('crypto', 'Cryptocurrency'),
    ]
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default='bank_transfer')

    allow_cancellation_fee = models.BooleanField(default=False)
    
    paypal_email = models.EmailField(blank=True, null=True)

    bank_account_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=30, blank=True, null=True)
    bank_name = models.CharField(max_length=30, blank=True, null=True)

    crypto_wallet_address = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment settings for {self.user.username}"
    

class SupportTicket(models.Model):
    """
    Stores support tickets submitted by users.
    
    Users can submit tickets for various issues, which can later be reviewed and resolved by support staff.
    
    Attributes:
        user (User): The user who submitted the support ticket (ForeignKey, allowing multiple tickets per user).
        issue_type (str): The category of the issue (e.g., account, payment, technical, etc.).
        description (str): A detailed description of the issue.
        created_at (datetime): The timestamp when the ticket was created.
        resolved (bool): Indicates whether the issue has been resolved.
        resolution_notes (str): Optional notes on how the issue was resolved.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")

    ISSUE_TYPES = [
        ('account', 'Account Issue'),
        ('payment', 'Payment Issue'),
        ('technical', 'Technical Issue'),
        ('feature', 'Feature Request'),
        ('meeting', 'Meeting Issue'),
        ('review', 'Review Issue'),
        ('other', 'Other'),
    ] 
    issue_type = models.CharField(max_length=15, choices=ISSUE_TYPES)

    description = models.TextField(max_length=600)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Support ticket ({self.issue_type}) for {self.user.username}"

