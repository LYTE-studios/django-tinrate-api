from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models

from tinrate_api.utils import success_response, error_response
from .serializers import (
    UserSerializer, UserWithExpertProfileSerializer,
    UserProfileCompleteSerializer
)

User = get_user_model()


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update current user's profile information.
    """
    user = request.user
    
    if request.method == 'GET':
        # Use different serializer based on whether user is an expert
        if user.is_expert and hasattr(user, 'expert_profile'):
            serializer = UserWithExpertProfileSerializer(user)
        else:
            serializer = UserSerializer(user)
        
        return success_response({
            'user': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_user = serializer.save()
            
            # Use appropriate serializer for response
            if updated_user.is_expert and hasattr(updated_user, 'expert_profile'):
                response_serializer = UserWithExpertProfileSerializer(updated_user)
            else:
                response_serializer = UserSerializer(updated_user)
            
            return success_response({
                'user': response_serializer.data
            })
        
        return error_response(
            "Profile update failed",
            details=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    """
    Complete user profile setup.
    """
    user = request.user
    
    if user.profile_complete:
        return error_response(
            "Profile is already complete",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = UserProfileCompleteSerializer(data=request.data)
    if serializer.is_valid():
        updated_user = serializer.update(user, serializer.validated_data)
        
        response_serializer = UserSerializer(updated_user)
        return success_response({
            'user': response_serializer.data,
            'message': 'Profile completed successfully'
        })
    
    return error_response(
        "Profile completion failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """
    Get user statistics and activity summary.
    """
    user = request.user
    
    stats = {
        'profileComplete': user.profile_complete,
        'isEmailVerified': user.is_email_verified,
        'isExpert': user.is_expert,
        'memberSince': user.created_at.strftime('%Y-%m-%d'),
    }
    
    # Add expert-specific stats if user is an expert
    if user.is_expert and hasattr(user, 'expert_profile'):
        expert = user.expert_profile
        stats.update({
            'expertStats': {
                'isListed': expert.is_listed,
                'totalMeetings': expert.total_meetings,
                'totalMeetingTime': expert.total_meeting_time,
                'rating': expert.rating,
                'reviewCount': expert.review_count,
                'profileUrl': expert.profile_url
            }
        })
    
    # Add client-specific stats
    from meetings.models import Meeting
    client_meetings = Meeting.objects.filter(client=user)
    stats.update({
        'clientStats': {
            'totalMeetingsBooked': client_meetings.count(),
            'completedMeetings': client_meetings.filter(status='completed').count(),
            'upcomingMeetings': client_meetings.filter(status='scheduled').count()
        }
    })
    
    return success_response(stats)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Delete user account (soft delete by deactivating).
    """
    user = request.user
    
    # Soft delete by deactivating the account
    user.is_active = False
    user.save()
    
    # If user is an expert, unpublish their listing
    if user.is_expert and hasattr(user, 'expert_profile'):
        expert = user.expert_profile
        expert.unpublish_listing()
    
    # Cancel all upcoming meetings
    from meetings.models import Meeting
    upcoming_meetings = Meeting.objects.filter(
        models.Q(expert__user=user) | models.Q(client=user),
        status='scheduled'
    )
    for meeting in upcoming_meetings:
        meeting.cancel()
    
    return success_response({
        'message': 'Account deactivated successfully'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request):
    """
    Upload profile image (placeholder for file upload functionality).
    """
    # In a real implementation, this would handle file upload to cloud storage
    # For now, we'll just accept a URL
    
    image_url = request.data.get('imageUrl')
    if not image_url:
        return error_response(
            "Image URL required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    user.profile_image_url = image_url
    user.save()
    
    serializer = UserSerializer(user)
    return success_response({
        'user': serializer.data,
        'message': 'Profile image updated successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity(request):
    """
    Get user's recent activity.
    """
    user = request.user
    activities = []
    
    # Get recent meetings
    from meetings.models import Meeting
    recent_meetings = Meeting.objects.filter(
        models.Q(expert__user=user) | models.Q(client=user)
    ).order_by('-created_at')[:5]
    
    for meeting in recent_meetings:
        activity_type = 'expert_meeting' if hasattr(user, 'expert_profile') and meeting.expert.user == user else 'client_meeting'
        activities.append({
            'type': activity_type,
            'description': f"Meeting with {meeting.client.full_name if activity_type == 'expert_meeting' else meeting.expert.name}",
            'timestamp': meeting.created_at,
            'status': meeting.status
        })
    
    # Get recent reviews (if expert)
    if user.is_expert and hasattr(user, 'expert_profile'):
        from reviews.models import Review
        recent_reviews = Review.objects.filter(
            expert=user.expert_profile
        ).order_by('-created_at')[:3]
        
        for review in recent_reviews:
            activities.append({
                'type': 'review_received',
                'description': f"Received {review.rating}-star review from {review.reviewer.full_name}",
                'timestamp': review.created_at,
                'rating': review.rating
            })
    
    # Sort activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return success_response({
        'recentActivity': activities[:10]  # Return top 10 most recent
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_email(request):
    """
    Change user's email address (requires verification).
    """
    new_email = request.data.get('email')
    if not new_email:
        return error_response(
            "New email required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email is already taken
    if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
        return error_response(
            "Email already in use",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # In a real implementation, this would:
    # 1. Send verification email to new address
    # 2. Store pending email change
    # 3. Update email after verification
    
    user = request.user
    user.email = new_email
    user.is_email_verified = False  # Require re-verification
    user.save()
    
    return success_response({
        'message': 'Email updated successfully. Please verify your new email address.',
        'requiresEmailVerification': True
    })
