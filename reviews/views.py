from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from tinrate_api.utils import success_response, error_response
from .models import Review, ReviewSummary
from .serializers import (
    ReviewSerializer, CreateReviewSerializer, ReviewSummarySerializer,
    ExpertReviewsResponseSerializer
)
from experts.models import Expert
from meetings.models import Meeting
from notifications.models import Notification

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def get_expert_reviews(request, expert_id):
    """
    Get reviews for a specific expert.
    """
    expert = get_object_or_404(Expert, id=expert_id)
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 reviews per page
    
    # Get reviews for the expert
    reviews_queryset = Review.objects.filter(expert=expert).order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(reviews_queryset, limit)
    page_obj = paginator.get_page(page)
    
    # Serialize reviews
    review_serializer = ReviewSerializer(page_obj.object_list, many=True)
    
    # Get or create review summary
    summary, created = ReviewSummary.objects.get_or_create(expert=expert)
    if created or not summary.total_reviews:
        summary.update_summary()
    
    summary_serializer = ReviewSummarySerializer(summary)
    
    response_data = {
        'reviews': review_serializer.data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': paginator.count,
            'totalPages': paginator.num_pages
        },
        'summary': summary_serializer.data
    }
    
    return success_response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, meeting_id):
    """
    Submit a review after a meeting.
    """
    user = request.user
    
    # Get the meeting
    meeting = get_object_or_404(
        Meeting,
        id=meeting_id,
        status='completed'
    )
    
    # Check if user was part of this meeting
    if meeting.client != user and meeting.expert.user != user:
        return error_response(
            "You can only review meetings you participated in",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if review already exists for this meeting
    if hasattr(meeting, 'review'):
        return error_response(
            "Review already exists for this meeting",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create the review
    serializer = CreateReviewSerializer(
        data=request.data,
        context={'request': request, 'meeting': meeting}
    )
    
    if serializer.is_valid():
        review = serializer.save()
        
        # Create notification for expert
        Notification.create_review_received(review)
        
        response_serializer = ReviewSerializer(review)
        return success_response({
            'review': response_serializer.data
        }, status_code=status.HTTP_201_CREATED)
    
    return error_response(
        "Review creation failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_reviews(request):
    """
    Get reviews given by the current user.
    """
    user = request.user
    
    # Get reviews given by this user
    reviews = Review.objects.filter(reviewer=user).order_by('-created_at')
    
    serializer = ReviewSerializer(reviews, many=True)
    
    return success_response({
        'reviews': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_received_reviews(request):
    """
    Get reviews received by the current user (if they're an expert).
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Only experts can view received reviews",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    expert = user.expert_profile
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 10)), 50)
    
    # Get reviews for the expert
    reviews_queryset = Review.objects.filter(expert=expert).order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(reviews_queryset, limit)
    page_obj = paginator.get_page(page)
    
    # Serialize reviews
    review_serializer = ReviewSerializer(page_obj.object_list, many=True)
    
    # Get review summary
    summary, created = ReviewSummary.objects.get_or_create(expert=expert)
    if created or not summary.total_reviews:
        summary.update_summary()
    
    summary_serializer = ReviewSummarySerializer(summary)
    
    response_data = {
        'reviews': review_serializer.data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': paginator.count,
            'totalPages': paginator.num_pages
        },
        'summary': summary_serializer.data
    }
    
    return success_response(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_review(request, review_id):
    """
    Update a review (only by the reviewer).
    """
    user = request.user
    
    review = get_object_or_404(Review, id=review_id, reviewer=user)
    
    serializer = CreateReviewSerializer(
        review,
        data=request.data,
        partial=True,
        context={'request': request, 'meeting': review.meeting}
    )
    
    if serializer.is_valid():
        updated_review = serializer.save()
        
        response_serializer = ReviewSerializer(updated_review)
        return success_response({
            'review': response_serializer.data
        })
    
    return error_response(
        "Review update failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    """
    Delete a review (only by the reviewer).
    """
    user = request.user
    
    review = get_object_or_404(Review, id=review_id, reviewer=user)
    expert = review.expert
    
    review.delete()
    
    # Update review summary
    ReviewSummary.update_for_expert(expert)
    
    return success_response({
        'message': 'Review deleted successfully'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_review_stats(request, expert_id):
    """
    Get review statistics for an expert.
    """
    expert = get_object_or_404(Expert, id=expert_id)
    
    # Get or create review summary
    summary, created = ReviewSummary.objects.get_or_create(expert=expert)
    if created or not summary.total_reviews:
        summary.update_summary()
    
    stats = {
        'averageRating': float(summary.average_rating),
        'totalReviews': summary.total_reviews,
        'ratingDistribution': summary.rating_distribution,
        'fiveStarCount': summary.rating_distribution.get('5', 0),
        'fourStarCount': summary.rating_distribution.get('4', 0),
        'threeStarCount': summary.rating_distribution.get('3', 0),
        'twoStarCount': summary.rating_distribution.get('2', 0),
        'oneStarCount': summary.rating_distribution.get('1', 0),
    }
    
    return success_response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_reviews(request):
    """
    Get meetings that are eligible for review by the current user.
    """
    user = request.user
    
    # Get completed meetings where user hasn't left a review yet
    completed_meetings = Meeting.objects.filter(
        client=user,
        status='completed'
    ).exclude(
        id__in=Review.objects.filter(reviewer=user).values_list('meeting_id', flat=True)
    ).order_by('-scheduled_at')
    
    pending_reviews = []
    for meeting in completed_meetings:
        pending_reviews.append({
            'meetingId': str(meeting.id),
            'expertName': meeting.expert.name,
            'expertId': str(meeting.expert.id),
            'meetingDate': meeting.scheduled_at.strftime('%Y-%m-%d'),
            'duration': meeting.duration
        })
    
    return success_response({
        'pendingReviews': pending_reviews
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flag_review(request, review_id):
    """
    Flag a review as inappropriate (admin functionality).
    """
    user = request.user
    
    # In a real implementation, this would be restricted to admins
    # For now, any authenticated user can flag reviews
    
    review = get_object_or_404(Review, id=review_id)
    reason = request.data.get('reason', '')
    
    # In a real implementation, this would create a flag record
    # For now, we'll just return success
    
    return success_response({
        'message': 'Review flagged successfully'
    })
