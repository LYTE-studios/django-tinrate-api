from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from tinrate_api.utils import success_response, error_response
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    MarkNotificationReadSerializer, BulkMarkReadSerializer,
    NotificationPreferenceSerializer, CreateNotificationSerializer
)

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get user notifications.
    """
    user = request.user
    unread_only = request.GET.get('unread', '').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    # Get notifications for the user
    queryset = Notification.objects.filter(user=user)
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    notifications = queryset.order_by('-created_at')[:limit]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    # Serialize data
    notification_serializer = NotificationSerializer(notifications, many=True)
    
    response_data = {
        'notifications': notification_serializer.data,
        'unreadCount': unread_count
    }
    
    return success_response(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark notification as read.
    """
    user = request.user
    
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=user
    )
    
    serializer = MarkNotificationReadSerializer()
    serializer.update(notification, {})
    
    return success_response({
        'message': 'Notification marked as read'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_mark_read(request):
    """
    Mark multiple notifications as read.
    """
    user = request.user
    serializer = BulkMarkReadSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        notification_ids = serializer.validated_data.get('notificationIds')
        
        if notification_ids:
            # Mark specific notifications as read
            Notification.objects.filter(
                id__in=notification_ids,
                user=user
            ).update(is_read=True)
            count = len(notification_ids)
        else:
            # Mark all notifications as read
            count = Notification.objects.filter(
                user=user,
                is_read=False
            ).update(is_read=True)
        
        return success_response({
            'message': f'{count} notifications marked as read'
        })
    
    return error_response(
        "Bulk mark read failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    Delete a notification.
    """
    user = request.user
    
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=user
    )
    
    notification.delete()
    
    return success_response({
        'message': 'Notification deleted successfully'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_delete_notifications(request):
    """
    Delete multiple notifications.
    """
    user = request.user
    notification_ids = request.data.get('notificationIds', [])
    
    if not notification_ids:
        return error_response(
            "Notification IDs required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete notifications
    count = Notification.objects.filter(
        id__in=notification_ids,
        user=user
    ).delete()[0]
    
    return success_response({
        'message': f'{count} notifications deleted successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_preferences(request):
    """
    Get user's notification preferences.
    """
    user = request.user
    
    # Get or create notification preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=user)
    
    serializer = NotificationPreferenceSerializer(preferences)
    
    return success_response({
        'preferences': serializer.data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_notification_preferences(request):
    """
    Update user's notification preferences.
    """
    user = request.user
    
    # Get or create notification preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=user)
    
    serializer = NotificationPreferenceSerializer(
        preferences,
        data=request.data,
        partial=True
    )
    
    if serializer.is_valid():
        updated_preferences = serializer.save()
        
        response_serializer = NotificationPreferenceSerializer(updated_preferences)
        return success_response({
            'preferences': response_serializer.data
        })
    
    return error_response(
        "Notification preferences update failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_stats(request):
    """
    Get notification statistics for the user.
    """
    user = request.user
    
    total_notifications = Notification.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    read_notifications = total_notifications - unread_notifications
    
    # Get notifications by type
    notifications_by_type = {}
    for notification_type, _ in Notification.TYPE_CHOICES:
        count = Notification.objects.filter(user=user, type=notification_type).count()
        if count > 0:
            notifications_by_type[notification_type] = count
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    recent_serializer = NotificationSerializer(recent_notifications, many=True)
    
    stats = {
        'totalNotifications': total_notifications,
        'unreadNotifications': unread_notifications,
        'readNotifications': read_notifications,
        'notificationsByType': notifications_by_type,
        'recentNotifications': recent_serializer.data
    }
    
    return success_response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    """
    Create a notification (admin/system use).
    """
    # In a real implementation, this would be restricted to admin users
    # For now, we'll allow any authenticated user to create notifications for themselves
    
    serializer = CreateNotificationSerializer(
        data=request.data,
        context={'user': request.user}
    )
    
    if serializer.is_valid():
        notification = serializer.save()
        
        response_serializer = NotificationSerializer(notification)
        return success_response({
            'notification': response_serializer.data
        }, status_code=status.HTTP_201_CREATED)
    
    return error_response(
        "Notification creation failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications(request):
    """
    Clear all notifications for the user.
    """
    user = request.user
    
    count = Notification.objects.filter(user=user).delete()[0]
    
    return success_response({
        'message': f'{count} notifications cleared successfully'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """
    Mark all notifications as read for the user.
    """
    user = request.user
    
    count = Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)
    
    return success_response({
        'message': f'{count} notifications marked as read'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """
    Get the count of unread notifications.
    """
    user = request.user
    
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    return success_response({
        'unreadCount': unread_count
    })
