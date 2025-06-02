from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review, ReviewSummary

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """
    id = serializers.CharField(read_only=True)
    reviewerId = serializers.CharField(source='reviewer_id', read_only=True)
    reviewerName = serializers.CharField(source='reviewer_name', read_only=True)
    reviewerType = serializers.CharField(source='reviewer_type', read_only=True)
    reviewerImageUrl = serializers.URLField(source='reviewer_image_url', read_only=True)
    meetingId = serializers.CharField(source='meeting_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'reviewerId', 'reviewerName', 'reviewerType',
            'reviewerImageUrl', 'rating', 'comment', 'meetingId', 'createdAt'
        ]


class CreateReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        """Create a review for a meeting."""
        meeting = self.context['meeting']
        reviewer = self.context['request'].user
        
        # Determine expert based on who is reviewing
        if hasattr(reviewer, 'expert_profile') and meeting.expert.user == reviewer:
            # Expert is reviewing the client (not typical, but possible)
            expert = meeting.expert
        else:
            # Client is reviewing the expert
            expert = meeting.expert
        
        review = Review.objects.create(
            expert=expert,
            reviewer=reviewer,
            meeting=meeting,
            **validated_data
        )
        
        # Update review summary for the expert
        ReviewSummary.update_for_expert(expert)
        
        return review


class ReviewSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for Review Summary.
    """
    averageRating = serializers.DecimalField(
        source='average_rating',
        max_digits=3,
        decimal_places=2,
        read_only=True
    )
    totalReviews = serializers.IntegerField(source='total_reviews', read_only=True)
    ratingDistribution = serializers.JSONField(source='rating_distribution', read_only=True)

    class Meta:
        model = ReviewSummary
        fields = ['averageRating', 'totalReviews', 'ratingDistribution']


class ExpertReviewsResponseSerializer(serializers.Serializer):
    """
    Serializer for expert reviews response with pagination and summary.
    """
    reviews = ReviewSerializer(many=True, read_only=True)
    pagination = serializers.DictField(read_only=True)
    summary = ReviewSummarySerializer(read_only=True)


class ReviewStatsSerializer(serializers.Serializer):
    """
    Serializer for review statistics.
    """
    averageRating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    totalReviews = serializers.IntegerField(read_only=True)
    fiveStarCount = serializers.IntegerField(read_only=True)
    fourStarCount = serializers.IntegerField(read_only=True)
    threeStarCount = serializers.IntegerField(read_only=True)
    twoStarCount = serializers.IntegerField(read_only=True)
    oneStarCount = serializers.IntegerField(read_only=True)
    ratingDistribution = serializers.DictField(read_only=True)


class UpdateReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for updating reviews.
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def update(self, instance, validated_data):
        """Update review and refresh summary."""
        review = super().update(instance, validated_data)
        
        # Update review summary for the expert
        ReviewSummary.update_for_expert(review.expert)
        
        return review


class ReviewResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for review responses (if experts can respond to reviews).
    """
    response = serializers.CharField(max_length=500, allow_blank=True)
    responseDate = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Review
        fields = ['response', 'responseDate']


class ReviewFilterSerializer(serializers.Serializer):
    """
    Serializer for review filtering parameters.
    """
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    dateFrom = serializers.DateField(required=False)
    dateTo = serializers.DateField(required=False)
    reviewerType = serializers.ChoiceField(
        choices=['Expert', 'Client'],
        required=False
    )

    def validate(self, data):
        """Validate date range."""
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("dateFrom must be before dateTo.")
        
        return data


class BulkReviewActionSerializer(serializers.Serializer):
    """
    Serializer for bulk review actions (admin functionality).
    """
    reviewIds = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'flag', 'unflag']
    )
    reason = serializers.CharField(required=False, allow_blank=True)