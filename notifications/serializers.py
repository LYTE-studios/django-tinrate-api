from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    id = serializers.CharField(read_only=True)
    actionUrl = serializers.URLField(source='action_url', read_only=True)
    isRead = serializers.BooleanField(source='is_read', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'isRead', 'createdAt', 'actionUrl'
        ]


class NotificationListSerializer(serializers.Serializer):
    """
    Serializer for notification list response.
    """
    notifications = NotificationSerializer(many=True, read_only=True)
    unreadCount = serializers.IntegerField(read_only=True)


class MarkNotificationReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    def update(self, instance, validated_data):
        """Mark notification as read."""
        instance.mark_as_read()
        return instance


class BulkMarkReadSerializer(serializers.Serializer):
    """
    Serializer for bulk marking notifications as read.
    """
    notificationIds = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )

    def validate_notificationIds(self, value):
        """Validate that all notification IDs exist and belong to the user."""
        if value:
            user = self.context['request'].user
            existing_ids = set(
                Notification.objects.filter(
                    id__in=value,
                    user=user
                ).values_list('id', flat=True)
            )
            
            provided_ids = set(value)
            invalid_ids = provided_ids - existing_ids
            
            if invalid_ids:
                raise serializers.ValidationError(
                    f"Invalid notification IDs: {list(invalid_ids)}"
                )
        
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification Preferences.
    """
    emailNotifications = serializers.BooleanField(source='email_notifications')
    pushNotifications = serializers.BooleanField(source='push_notifications')
    meetingReminders = serializers.BooleanField(source='meeting_reminders')
    reviewNotifications = serializers.BooleanField(source='review_notifications')
    paymentNotifications = serializers.BooleanField(source='payment_notifications')
    marketingEmails = serializers.BooleanField(source='marketing_emails')

    class Meta:
        model = NotificationPreference
        fields = [
            'emailNotifications', 'pushNotifications', 'meetingReminders',
            'reviewNotifications', 'paymentNotifications', 'marketingEmails'
        ]

    def update(self, instance, validated_data):
        """Update notification preferences."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CreateNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications (admin/system use).
    """
    actionUrl = serializers.URLField(source='action_url', required=False, allow_null=True)
    meetingId = serializers.UUIDField(write_only=True, required=False)
    reviewId = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Notification
        fields = [
            'type', 'title', 'message', 'actionUrl', 'meetingId', 'reviewId'
        ]

    def validate_meetingId(self, value):
        """Validate meeting exists if provided."""
        if value:
            from meetings.models import Meeting
            try:
                return Meeting.objects.get(id=value)
            except Meeting.DoesNotExist:
                raise serializers.ValidationError("Meeting not found.")
        return None

    def validate_reviewId(self, value):
        """Validate review exists if provided."""
        if value:
            from reviews.models import Review
            try:
                return Review.objects.get(id=value)
            except Review.DoesNotExist:
                raise serializers.ValidationError("Review not found.")
        return None

    def create(self, validated_data):
        """Create notification with optional relationships."""
        meeting = validated_data.pop('meetingId', None)
        review = validated_data.pop('reviewId', None)
        user = self.context['user']
        
        notification = Notification.objects.create(
            user=user,
            meeting=meeting,
            review=review,
            **validated_data
        )
        return notification


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics.
    """
    totalNotifications = serializers.IntegerField(read_only=True)
    unreadNotifications = serializers.IntegerField(read_only=True)
    readNotifications = serializers.IntegerField(read_only=True)
    notificationsByType = serializers.DictField(read_only=True)
    recentNotifications = NotificationSerializer(many=True, read_only=True)


class NotificationFilterSerializer(serializers.Serializer):
    """
    Serializer for notification filtering parameters.
    """
    type = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        required=False
    )
    isRead = serializers.BooleanField(required=False)
    dateFrom = serializers.DateTimeField(required=False)
    dateTo = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)

    def validate(self, data):
        """Validate date range."""
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("dateFrom must be before dateTo.")
        
        return data


class DeleteNotificationSerializer(serializers.Serializer):
    """
    Serializer for deleting notifications.
    """
    def delete(self, instance):
        """Delete the notification."""
        instance.delete()
        return instance


class BulkDeleteNotificationsSerializer(serializers.Serializer):
    """
    Serializer for bulk deleting notifications.
    """
    notificationIds = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of notification IDs to delete."
    )

    def validate_notificationIds(self, value):
        """Validate that all notification IDs exist and belong to the user."""
        user = self.context['request'].user
        existing_ids = set(
            Notification.objects.filter(
                id__in=value,
                user=user
            ).values_list('id', flat=True)
        )
        
        provided_ids = set(value)
        invalid_ids = provided_ids - existing_ids
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid notification IDs: {list(invalid_ids)}"
            )
        
        return value