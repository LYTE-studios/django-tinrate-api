from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from tinrate_api.utils import success_response, error_response
from .models import Meeting, MeetingInvitation
from .serializers import (
    MeetingSerializer, UpcomingMeetingSerializer, MeetingInvitationSerializer,
    CreateMeetingInvitationSerializer, AcceptMeetingInvitationSerializer,
    DeclineMeetingInvitationSerializer, CancelMeetingSerializer,
    CompleteMeetingSerializer
)
from notifications.models import Notification

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meetings(request):
    """
    Get user's meetings (both as expert and client).
    """
    user = request.user
    meeting_type = request.GET.get('type', 'upcoming')  # upcoming, past, all
    limit = min(int(request.GET.get('limit', 10)), 100)
    
    # Get meetings where user is either expert or client
    queryset = Meeting.objects.filter(
        Q(expert__user=user) | Q(client=user)
    )
    
    # Filter by type
    if meeting_type == 'upcoming':
        queryset = queryset.filter(
            status='scheduled',
            scheduled_at__gte=timezone.now()
        ).order_by('scheduled_at')
    elif meeting_type == 'past':
        queryset = queryset.filter(
            Q(status='completed') | Q(status='cancelled') | Q(status='no_show') |
            Q(status='scheduled', scheduled_at__lt=timezone.now())
        ).order_by('-scheduled_at')
    else:  # all
        queryset = queryset.order_by('-scheduled_at')
    
    # Limit results
    meetings = queryset[:limit]
    
    # Serialize data
    serializer = MeetingSerializer(meetings, many=True, context={'request': request})
    
    return success_response({
        'meetings': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_detail(request, meeting_id):
    """
    Get detailed information about a specific meeting.
    """
    user = request.user
    
    # Get meeting where user is either expert or client
    meeting = get_object_or_404(
        Meeting,
        Q(expert__user=user) | Q(client=user),
        id=meeting_id
    )
    
    serializer = MeetingSerializer(meeting, context={'request': request})
    
    return success_response({
        'meeting': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_meeting_invitation(request):
    """
    Create a meeting invitation (book a meeting with an expert).
    """
    serializer = CreateMeetingInvitationSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        invitation = serializer.save()
        
        # Create notification for expert
        Notification.create_meeting_scheduled(invitation)
        
        response_serializer = MeetingInvitationSerializer(invitation)
        return success_response({
            'invitation': response_serializer.data
        }, status_code=status.HTTP_201_CREATED)
    
    return error_response(
        "Meeting invitation creation failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_invitations(request):
    """
    Get meeting invitations for the current user.
    """
    user = request.user
    invitation_type = request.GET.get('type', 'received')  # received, sent
    
    if invitation_type == 'received':
        # Invitations received by expert
        if not hasattr(user, 'expert_profile'):
            return success_response({'invitations': []})
        
        invitations = MeetingInvitation.objects.filter(
            expert=user.expert_profile
        ).order_by('-created_at')
    else:  # sent
        # Invitations sent by client
        invitations = MeetingInvitation.objects.filter(
            client=user
        ).order_by('-created_at')
    
    serializer = MeetingInvitationSerializer(invitations, many=True)
    
    return success_response({
        'invitations': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_meeting_invitation(request, invitation_id):
    """
    Accept a meeting invitation (expert accepts client's request).
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Only experts can accept meeting invitations",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    invitation = get_object_or_404(
        MeetingInvitation,
        id=invitation_id,
        expert=user.expert_profile,
        status='pending'
    )
    
    serializer = AcceptMeetingInvitationSerializer()
    meeting = serializer.update(invitation, {})
    
    if meeting:
        # Create notifications
        Notification.create_meeting_scheduled(meeting)
        
        meeting_serializer = MeetingSerializer(meeting, context={'request': request})
        return success_response({
            'meeting': meeting_serializer.data,
            'message': 'Meeting invitation accepted successfully'
        })
    
    return error_response(
        "Failed to accept meeting invitation",
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_meeting_invitation(request, invitation_id):
    """
    Decline a meeting invitation.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Only experts can decline meeting invitations",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    invitation = get_object_or_404(
        MeetingInvitation,
        id=invitation_id,
        expert=user.expert_profile,
        status='pending'
    )
    
    serializer = DeclineMeetingInvitationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(invitation, serializer.validated_data)
        
        return success_response({
            'message': 'Meeting invitation declined successfully'
        })
    
    return error_response(
        "Failed to decline meeting invitation",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_meeting(request, meeting_id):
    """
    Cancel a scheduled meeting.
    """
    user = request.user
    
    # Get meeting where user is either expert or client
    meeting = get_object_or_404(
        Meeting,
        Q(expert__user=user) | Q(client=user),
        id=meeting_id,
        status='scheduled'
    )
    
    serializer = CancelMeetingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(meeting, serializer.validated_data)
        
        # Create notification for the other party
        Notification.create_meeting_cancelled(meeting, user)
        
        return success_response({
            'message': 'Meeting cancelled successfully'
        })
    
    return error_response(
        "Failed to cancel meeting",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_meeting(request, meeting_id):
    """
    Mark a meeting as completed.
    """
    user = request.user
    
    # Only experts can mark meetings as completed
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Only experts can mark meetings as completed",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    meeting = get_object_or_404(
        Meeting,
        expert=user.expert_profile,
        id=meeting_id,
        status='scheduled'
    )
    
    serializer = CompleteMeetingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(meeting, serializer.validated_data)
        
        return success_response({
            'message': 'Meeting marked as completed successfully'
        })
    
    return error_response(
        "Failed to complete meeting",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_stats(request):
    """
    Get meeting statistics for the current user.
    """
    user = request.user
    
    stats = {}
    
    # Client stats
    client_meetings = Meeting.objects.filter(client=user)
    stats['clientStats'] = {
        'totalMeetings': client_meetings.count(),
        'completedMeetings': client_meetings.filter(status='completed').count(),
        'upcomingMeetings': client_meetings.filter(
            status='scheduled',
            scheduled_at__gte=timezone.now()
        ).count(),
        'cancelledMeetings': client_meetings.filter(status='cancelled').count()
    }
    
    # Expert stats (if user is an expert)
    if hasattr(user, 'expert_profile'):
        expert_meetings = Meeting.objects.filter(expert=user.expert_profile)
        stats['expertStats'] = {
            'totalMeetings': expert_meetings.count(),
            'completedMeetings': expert_meetings.filter(status='completed').count(),
            'upcomingMeetings': expert_meetings.filter(
                status='scheduled',
                scheduled_at__gte=timezone.now()
            ).count(),
            'cancelledMeetings': expert_meetings.filter(status='cancelled').count(),
            'totalHours': user.expert_profile.total_hours,
            'averageRating': user.expert_profile.rating
        }
    
    return success_response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reschedule_meeting(request, meeting_id):
    """
    Request to reschedule a meeting.
    """
    user = request.user
    new_time = request.data.get('scheduledAt')
    
    if not new_time:
        return error_response(
            "New meeting time required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Get meeting where user is either expert or client
    meeting = get_object_or_404(
        Meeting,
        Q(expert__user=user) | Q(client=user),
        id=meeting_id,
        status='scheduled'
    )
    
    # In a real implementation, this might create a reschedule request
    # For now, we'll directly update the meeting time
    try:
        from datetime import datetime
        meeting.scheduled_at = datetime.fromisoformat(new_time.replace('Z', '+00:00'))
        meeting.save()
        
        # Create notification for the other party
        other_user = meeting.client if meeting.expert.user == user else meeting.expert.user
        Notification.objects.create(
            user=other_user,
            type='meeting_scheduled',
            title='Meeting rescheduled',
            message=f'Your meeting has been rescheduled to {meeting.scheduled_at.strftime("%Y-%m-%d %H:%M")}',
            action_url=f'/meetings/{meeting.id}',
            meeting=meeting
        )
        
        serializer = MeetingSerializer(meeting, context={'request': request})
        return success_response({
            'meeting': serializer.data,
            'message': 'Meeting rescheduled successfully'
        })
    
    except ValueError:
        return error_response(
            "Invalid date format",
            status_code=status.HTTP_400_BAD_REQUEST
        )
