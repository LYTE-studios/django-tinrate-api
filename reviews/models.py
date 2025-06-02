from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Review(models.Model):
    """
    Model to represent reviews and ratings for experts.
    """
    REVIEWER_TYPE_CHOICES = [
        ('Expert', 'Expert'),
        ('Client', 'Client'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expert = models.ForeignKey(
        'experts.Expert',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )
    meeting = models.OneToOneField(
        'meetings.Meeting',
        on_delete=models.CASCADE,
        related_name='review'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        help_text="Review comment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['meeting'],
                name='unique_review_per_meeting'
            )
        ]

    def __str__(self):
        return f"Review for {self.expert.name} by {self.reviewer.full_name}"

    @property
    def reviewer_name(self):
        """Return the reviewer's name."""
        return self.reviewer.full_name

    @property
    def reviewer_type(self):
        """Determine if the reviewer is an expert or client."""
        if hasattr(self.reviewer, 'expert_profile'):
            return 'Expert'
        return 'Client'

    @property
    def reviewer_image_url(self):
        """Return the reviewer's profile image URL."""
        return self.reviewer.profile_image_url

    @property
    def reviewer_id(self):
        """Return the reviewer's ID."""
        return str(self.reviewer.id)

    @property
    def meeting_id(self):
        """Return the meeting ID."""
        return str(self.meeting.id)


class ReviewSummary(models.Model):
    """
    Model to store aggregated review statistics for experts.
    This is updated whenever reviews are added/modified for performance.
    """
    expert = models.OneToOneField(
        'experts.Expert',
        on_delete=models.CASCADE,
        related_name='review_summary'
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text="Average rating for this expert"
    )
    total_reviews = models.PositiveIntegerField(
        default=0,
        help_text="Total number of reviews"
    )
    rating_distribution = models.JSONField(
        default=dict,
        help_text="Distribution of ratings (1-5 stars)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_summaries'
        verbose_name = 'Review Summary'
        verbose_name_plural = 'Review Summaries'

    def __str__(self):
        return f"Review Summary for {self.expert.name}"

    def update_summary(self):
        """Update the review summary statistics."""
        from django.db.models import Avg, Count
        
        reviews = Review.objects.filter(expert=self.expert)
        
        # Calculate average rating
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        self.average_rating = round(avg_rating, 2)
        
        # Count total reviews
        self.total_reviews = reviews.count()
        
        # Calculate rating distribution
        distribution = {str(i): 0 for i in range(1, 6)}
        rating_counts = reviews.values('rating').annotate(count=Count('rating'))
        
        for item in rating_counts:
            distribution[str(item['rating'])] = item['count']
        
        self.rating_distribution = distribution
        self.save()

    @classmethod
    def update_for_expert(cls, expert):
        """Update or create review summary for an expert."""
        summary, created = cls.objects.get_or_create(expert=expert)
        summary.update_summary()
        return summary
