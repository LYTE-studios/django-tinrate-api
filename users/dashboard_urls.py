from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from tinrate_api.utils import success_response
from users.serializers import UserSerializer
from meetings.models import Meeting
from meetings.serializers import UpcomingMeetingSerializer

app_name = 'dashboard'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """
    Get comprehensive dashboard data (optimized single request).
    """
    user = request.user
    
    # Basic user data
    user_data = {
        'id': str(user.id),
        'firstName': user.first_name,
        'lastName': user.last_name,
        'isExpert': user.is_expert
    }
    
    # Expert stats (if user is an expert)
    expert_stats = None
    if user.is_expert and hasattr(user, 'expert_profile'):
        expert = user.expert_profile
        expert_stats = {
            'totalMeetings': expert.total_meetings,
            'totalMeetingTime': expert.total_meeting_time,
            'rating': expert.rating,
            'reviewCount': expert.review_count,
            'isListed': expert.is_listed
        }
    
    # Upcoming meetings
    upcoming_meetings_queryset = Meeting.objects.filter(
        Q(expert__user=user) | Q(client=user),
        status='scheduled',
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')[:5]
    
    upcoming_meetings_serializer = UpcomingMeetingSerializer(
        upcoming_meetings_queryset,
        many=True,
        context={'request': request}
    )
    
    # Recent activity
    recent_activity = []
    
    # Get recent completed meetings
    recent_meetings = Meeting.objects.filter(
        Q(expert__user=user) | Q(client=user),
        status='completed'
    ).order_by('-scheduled_at')[:3]
    
    for meeting in recent_meetings:
        activity_type = 'expert_meeting' if hasattr(user, 'expert_profile') and meeting.expert.user == user else 'client_meeting'
        other_person = meeting.client.full_name if activity_type == 'expert_meeting' else meeting.expert.name
        
        recent_activity.append({
            'type': 'meeting_completed',
            'description': f'Meeting with {other_person} completed',
            'timestamp': meeting.scheduled_at.isoformat()
        })
    
    # Get recent reviews (if expert)
    if user.is_expert and hasattr(user, 'expert_profile'):
        from reviews.models import Review
        recent_reviews = Review.objects.filter(
            expert=user.expert_profile
        ).order_by('-created_at')[:2]
        
        for review in recent_reviews:
            recent_activity.append({
                'type': 'review_received',
                'description': f'Received {review.rating}-star review from {review.reviewer.full_name}',
                'timestamp': review.created_at.isoformat()
            })
    
    # Sort activity by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Prepare response data
    dashboard_data = {
        'user': user_data,
        'upcomingMeetings': upcoming_meetings_serializer.data,
        'recentActivity': recent_activity[:5]  # Limit to 5 most recent
    }
    
    if expert_stats:
        dashboard_data['expertStats'] = expert_stats
    
    return success_response(dashboard_data)


urlpatterns = [
    path('', get_dashboard_data, name='get_dashboard_data'),
]