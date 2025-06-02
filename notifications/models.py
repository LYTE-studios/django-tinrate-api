from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    """
    Model to represent user notifications.
    """
    TYPE_CHOICES = [
        ('meeting_reminder', 'Meeting Reminder'),
        ('meeting_scheduled', 'Meeting Scheduled'),
        ('meeting_cancelled', 'Meeting Cancelled'),
        ('meeting_completed', 'Meeting Completed'),
        ('review_received', 'Review Received'),
        ('profile_approved', 'Profile Approved'),
        ('profile_rejected', 'Profile Rejected'),
        ('payment_received', 'Payment Received'),
        ('system_announcement', 'System Announcement'),
        ('expert_application', 'Expert Application'),
        ('general', 'General'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type of notification"
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message"
    )
    action_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to navigate to when notification is clicked"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional foreign key relationships for context
    meeting = models.ForeignKey(
        'meetings.Meeting',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    review = models.ForeignKey(
        'reviews.Review',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def create_meeting_reminder(cls, meeting, hours_before=1):
        """Create a meeting reminder notification."""
        return cls.objects.create(
            user=meeting.client,
            type='meeting_reminder',
            title=f'Meeting in {hours_before} hour{"s" if hours_before != 1 else ""}',
            message=f'Your meeting with {meeting.expert.name} starts in {hours_before} hour{"s" if hours_before != 1 else ""}',
            action_url=f'/meetings/{meeting.id}',
            meeting=meeting
        )

    @classmethod
    def create_meeting_scheduled(cls, meeting):
        """Create a meeting scheduled notification."""
        # Notify the expert
        cls.objects.create(
            user=meeting.expert.user,
            type='meeting_scheduled',
            title='New meeting scheduled',
            message=f'You have a new meeting scheduled with {meeting.client.full_name}',
            action_url=f'/meetings/{meeting.id}',
            meeting=meeting
        )
        
        # Notify the client
        cls.objects.create(
            user=meeting.client,
            type='meeting_scheduled',
            title='Meeting confirmed',
            message=f'Your meeting with {meeting.expert.name} has been confirmed',
            action_url=f'/meetings/{meeting.id}',
            meeting=meeting
        )

    @classmethod
    def create_meeting_cancelled(cls, meeting, cancelled_by):
        """Create a meeting cancelled notification."""
        other_user = meeting.client if cancelled_by == meeting.expert.user else meeting.expert.user
        
        cls.objects.create(
            user=other_user,
            type='meeting_cancelled',
            title='Meeting cancelled',
            message=f'Your meeting with {cancelled_by.full_name} has been cancelled',
            action_url=f'/meetings/{meeting.id}',
            meeting=meeting
        )

    @classmethod
    def create_review_received(cls, review):
        """Create a review received notification."""
        cls.objects.create(
            user=review.expert.user,
            type='review_received',
            title='New review received',
            message=f'You received a new {review.rating}-star review from {review.reviewer.full_name}',
            action_url=f'/experts/{review.expert.profile_url}',
            review=review
        )

    @classmethod
    def create_payment_received(cls, user, amount, meeting):
        """Create a payment received notification."""
        cls.objects.create(
            user=user,
            type='payment_received',
            title='Payment received',
            message=f'You received ${amount} for your meeting with {meeting.client.full_name}',
            action_url='/billing/overview',
            meeting=meeting
        )


class NotificationPreference(models.Model):
    """
    Model to store user notification preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications"
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text="Receive push notifications"
    )
    meeting_reminders = models.BooleanField(
        default=True,
        help_text="Receive meeting reminder notifications"
    )
    review_notifications = models.BooleanField(
        default=True,
        help_text="Receive review notifications"
    )
    payment_notifications = models.BooleanField(
        default=True,
        help_text="Receive payment notifications"
    )
    marketing_emails = models.BooleanField(
        default=False,
        help_text="Receive marketing emails"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Notification preferences for {self.user.email}"
