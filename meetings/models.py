from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class Meeting(models.Model):
    """
    Model to represent meetings between experts and clients.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey(
        'experts.Expert',
        on_delete=models.CASCADE,
        related_name='expert_meetings'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_meetings'
    )
    scheduled_at = models.DateTimeField(
        help_text="When the meeting is scheduled"
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(15)],
        help_text="Meeting duration in minutes"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the meeting"
    )
    meeting_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for the video meeting"
    )
    notes = models.TextField(
        blank=True,
        help_text="Meeting notes or agenda"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Meeting: {self.expert.name} with {self.client.full_name}"

    @property
    def expert_name(self):
        """Return the expert's name."""
        return self.expert.name

    @property
    def client_name(self):
        """Return the client's name."""
        return self.client.full_name

    @property
    def expert_id(self):
        """Return the expert's ID."""
        return str(self.expert.id)

    @property
    def client_id(self):
        """Return the client's ID."""
        return str(self.client.id)

    def generate_meeting_url(self):
        """Generate a meeting URL for this meeting."""
        # In a real implementation, this would integrate with a video conferencing service
        self.meeting_url = f"https://meet.tinrate.com/{self.id}"
        self.save(update_fields=['meeting_url'])
        return self.meeting_url

    def mark_completed(self):
        """Mark the meeting as completed."""
        self.status = 'completed'
        self.save(update_fields=['status'])

    def cancel(self):
        """Cancel the meeting."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])


class MeetingInvitation(models.Model):
    """
    Model to handle meeting invitations and booking requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey(
        'experts.Expert',
        on_delete=models.CASCADE,
        related_name='meeting_invitations'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    requested_at = models.DateTimeField(
        help_text="Requested meeting time"
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(15)],
        help_text="Requested meeting duration in minutes"
    )
    message = models.TextField(
        blank=True,
        help_text="Message from client to expert"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the invitation"
    )
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invitation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meeting_invitations'
        verbose_name = 'Meeting Invitation'
        verbose_name_plural = 'Meeting Invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation: {self.client.full_name} to {self.expert.name}"

    def accept(self):
        """Accept the meeting invitation and create a meeting."""
        if self.status == 'pending':
            # Create the meeting
            meeting = Meeting.objects.create(
                expert=self.expert,
                client=self.client,
                scheduled_at=self.requested_at,
                duration=self.duration,
                status='scheduled'
            )
            meeting.generate_meeting_url()
            
            # Update invitation status
            self.status = 'accepted'
            self.meeting = meeting
            self.save(update_fields=['status', 'meeting'])
            
            return meeting
        return None

    def decline(self):
        """Decline the meeting invitation."""
        if self.status == 'pending':
            self.status = 'declined'
            self.save(update_fields=['status'])

    def expire(self):
        """Mark the invitation as expired."""
        if self.status == 'pending':
            self.status = 'expired'
            self.save(update_fields=['status'])
