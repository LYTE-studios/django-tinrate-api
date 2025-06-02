from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Meeting, MeetingInvitation

User = get_user_model()


class MeetingSerializer(serializers.ModelSerializer):
    """
    Serializer for Meeting model.
    """
    id = serializers.CharField(read_only=True)
    expertId = serializers.CharField(source='expert_id', read_only=True)
    expertName = serializers.CharField(read_only=True)
    clientId = serializers.CharField(source='client_id', read_only=True)
    clientName = serializers.CharField(read_only=True)
    scheduledAt = serializers.DateTimeField(source='scheduled_at')
    meetingUrl = serializers.URLField(source='meeting_url', read_only=True)
    type = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            'id', 'expertId', 'expertName', 'clientId', 'clientName',
            'scheduledAt', 'duration', 'status', 'meetingUrl', 'type'
        ]

    def get_type(self, obj):
        """Determine if this is an expert or client meeting from the user's perspective."""
        request = self.context.get('request')
        if request and request.user:
            if hasattr(request.user, 'expert_profile') and obj.expert.user == request.user:
                return 'expert'
            elif obj.client == request.user:
                return 'client'
        return 'client'


class UpcomingMeetingSerializer(serializers.ModelSerializer):
    """
    Serializer for upcoming meetings in dashboard and profile views.
    """
    id = serializers.CharField(read_only=True)
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    clientName = serializers.CharField(source='client_name', read_only=True)
    expertName = serializers.CharField(source='expert_name', read_only=True)
    type = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = ['id', 'date', 'time', 'clientName', 'expertName', 'type']

    def get_date(self, obj):
        """Return the meeting date in YYYY-MM-DD format."""
        return obj.scheduled_at.strftime('%Y-%m-%d')

    def get_time(self, obj):
        """Return the meeting time in HH:MM format."""
        return obj.scheduled_at.strftime('%H:%M')

    def get_type(self, obj):
        """Determine if this is an expert or client meeting from the user's perspective."""
        request = self.context.get('request')
        if request and request.user:
            if hasattr(request.user, 'expert_profile') and obj.expert.user == request.user:
                return 'expert'
            elif obj.client == request.user:
                return 'client'
        return 'client'


class MeetingInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer for Meeting Invitation model.
    """
    id = serializers.CharField(read_only=True)
    expertId = serializers.CharField(source='expert.id', read_only=True)
    expertName = serializers.CharField(source='expert.name', read_only=True)
    clientId = serializers.CharField(source='client.id', read_only=True)
    clientName = serializers.CharField(source='client.full_name', read_only=True)
    requestedAt = serializers.DateTimeField(source='requested_at')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = MeetingInvitation
        fields = [
            'id', 'expertId', 'expertName', 'clientId', 'clientName',
            'requestedAt', 'duration', 'message', 'status', 'createdAt'
        ]


class CreateMeetingInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating meeting invitations.
    """
    expertId = serializers.UUIDField(write_only=True)
    requestedAt = serializers.DateTimeField(source='requested_at')

    class Meta:
        model = MeetingInvitation
        fields = ['expertId', 'requestedAt', 'duration', 'message']

    def validate_expertId(self, value):
        """Validate that expert exists."""
        from experts.models import Expert
        try:
            expert = Expert.objects.get(id=value)
            return expert
        except Expert.DoesNotExist:
            raise serializers.ValidationError("Expert not found.")

    def validate_duration(self, value):
        """Validate meeting duration."""
        from django.conf import settings
        valid_durations = getattr(settings, 'MEETING_DURATION_CHOICES', [15, 30, 45, 60, 90, 120])
        if value not in valid_durations:
            raise serializers.ValidationError(f"Duration must be one of: {valid_durations}")
        return value

    def create(self, validated_data):
        """Create a meeting invitation."""
        expert = validated_data.pop('expertId')
        client = self.context['request'].user
        
        invitation = MeetingInvitation.objects.create(
            expert=expert,
            client=client,
            **validated_data
        )
        return invitation


class AcceptMeetingInvitationSerializer(serializers.Serializer):
    """
    Serializer for accepting meeting invitations.
    """
    def update(self, instance, validated_data):
        """Accept the meeting invitation."""
        meeting = instance.accept()
        return meeting


class DeclineMeetingInvitationSerializer(serializers.Serializer):
    """
    Serializer for declining meeting invitations.
    """
    reason = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Decline the meeting invitation."""
        instance.decline()
        return instance


class CancelMeetingSerializer(serializers.Serializer):
    """
    Serializer for cancelling meetings.
    """
    reason = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Cancel the meeting."""
        instance.cancel()
        return instance


class CompleteMeetingSerializer(serializers.Serializer):
    """
    Serializer for marking meetings as completed.
    """
    notes = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Mark the meeting as completed."""
        if validated_data.get('notes'):
            instance.notes = validated_data['notes']
        instance.mark_completed()
        return instance


class MeetingStatsSerializer(serializers.Serializer):
    """
    Serializer for meeting statistics.
    """
    totalMeetings = serializers.IntegerField(read_only=True)
    completedMeetings = serializers.IntegerField(read_only=True)
    cancelledMeetings = serializers.IntegerField(read_only=True)
    totalHours = serializers.IntegerField(read_only=True)
    averageRating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)