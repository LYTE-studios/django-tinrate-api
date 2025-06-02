from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid


class Expert(models.Model):
    """
    Expert model that represents an expert's profile and listing information.
    """
    SKILL_CHOICES = [
        ('DESIGN', 'Design'),
        ('PROGRAMMING', 'Programming'),
        ('MARKETING', 'Marketing'),
        ('BUSINESS', 'Business'),
        ('DATA_SCIENCE', 'Data Science'),
        ('PRODUCT_MANAGEMENT', 'Product Management'),
        ('CONSULTING', 'Consulting'),
        ('FINANCE', 'Finance'),
        ('LEGAL', 'Legal'),
        ('SALES', 'Sales'),
        ('OPERATIONS', 'Operations'),
        ('HR', 'Human Resources'),
        ('EDUCATION', 'Education'),
        ('HEALTHCARE', 'Healthcare'),
        ('ENGINEERING', 'Engineering'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expert_profile'
    )
    title = models.CharField(
        max_length=200,
        help_text="Expert's professional title"
    )
    company = models.CharField(
        max_length=200,
        help_text="Expert's company name"
    )
    bio = models.TextField(
        max_length=settings.MAX_BIO_LENGTH,
        help_text="Expert's biography"
    )
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        help_text="Expert's hourly rate in USD"
    )
    skills = models.JSONField(
        default=list,
        help_text="List of expert's skills"
    )
    profile_url = models.SlugField(
        max_length=settings.MAX_PROFILE_URL_LENGTH,
        unique=True,
        help_text="Custom URL for expert's profile"
    )
    is_listed = models.BooleanField(
        default=False,
        help_text="Whether the expert is publicly listed"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether the expert is featured"
    )
    is_top_rated = models.BooleanField(
        default=False,
        help_text="Whether the expert is top-rated"
    )
    company_logo = models.URLField(
        blank=True,
        null=True,
        help_text="URL to company logo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'experts'
        verbose_name = 'Expert'
        verbose_name_plural = 'Experts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"

    @property
    def name(self):
        """Return the expert's full name."""
        return self.user.full_name

    @property
    def profile_image_url(self):
        """Return the expert's profile image URL."""
        return self.user.profile_image_url

    @property
    def rating(self):
        """Calculate the expert's average rating."""
        from reviews.models import Review
        reviews = Review.objects.filter(expert=self)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0

    @property
    def review_count(self):
        """Return the number of reviews for this expert."""
        from reviews.models import Review
        return Review.objects.filter(expert=self).count()

    @property
    def total_meetings(self):
        """Return the total number of completed meetings."""
        from meetings.models import Meeting
        return Meeting.objects.filter(
            expert=self,
            status='completed'
        ).count()

    @property
    def total_meeting_time(self):
        """Return the total meeting time in HH:MM format."""
        from meetings.models import Meeting
        from django.db.models import Sum
        
        total_minutes = Meeting.objects.filter(
            expert=self,
            status='completed'
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    @property
    def total_hours(self):
        """Return the total meeting hours."""
        from meetings.models import Meeting
        from django.db.models import Sum
        
        total_minutes = Meeting.objects.filter(
            expert=self,
            status='completed'
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0
        
        return total_minutes // 60

    @property
    def is_available_soon(self):
        """Check if the expert has availability in the next 7 days."""
        from django.utils import timezone
        from datetime import timedelta
        from .models import Availability
        
        next_week = timezone.now() + timedelta(days=7)
        return Availability.objects.filter(
            expert=self,
            date__lte=next_week.date(),
            is_available=True
        ).exists()

    def publish_listing(self):
        """Publish the expert listing."""
        self.is_listed = True
        self.save(update_fields=['is_listed'])

    def unpublish_listing(self):
        """Unpublish the expert listing."""
        self.is_listed = False
        self.save(update_fields=['is_listed'])


class Availability(models.Model):
    """
    Model to store expert availability schedules.
    """
    WEEKDAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey(
        Expert,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Specific date (for date-specific availability)"
    )
    weekday = models.CharField(
        max_length=10,
        choices=WEEKDAY_CHOICES,
        null=True,
        blank=True,
        help_text="Weekday (for weekly default availability)"
    )
    start_time = models.TimeField(
        help_text="Start time of availability slot"
    )
    end_time = models.TimeField(
        help_text="End time of availability slot"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this time slot is available"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this time slot is enabled (for weekly defaults)"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="Timezone for this availability slot"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expert_availability'
        verbose_name = 'Expert Availability'
        verbose_name_plural = 'Expert Availability'
        ordering = ['date', 'weekday', 'start_time']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(date__isnull=False, weekday__isnull=True) |
                    models.Q(date__isnull=True, weekday__isnull=False)
                ),
                name='availability_date_or_weekday'
            )
        ]

    def __str__(self):
        if self.date:
            return f"{self.expert.name} - {self.date} {self.start_time}-{self.end_time}"
        return f"{self.expert.name} - {self.weekday} {self.start_time}-{self.end_time}"
