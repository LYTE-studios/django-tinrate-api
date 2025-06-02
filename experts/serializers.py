from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Expert, Availability
from reviews.models import Review

User = get_user_model()


class ExpertListSerializer(serializers.ModelSerializer):
    """
    Serializer for Expert listing in search results and featured lists.
    """
    id = serializers.CharField(read_only=True)
    userId = serializers.CharField(source='user.id', read_only=True)
    name = serializers.CharField(read_only=True)
    profileImageUrl = serializers.CharField(source='profile_image_url', read_only=True)
    hourlyRate = serializers.DecimalField(source='hourly_rate', max_digits=6, decimal_places=2, read_only=True)
    reviewCount = serializers.IntegerField(read_only=True)
    totalHours = serializers.IntegerField(read_only=True)
    isAvailableSoon = serializers.BooleanField(source='is_available_soon', read_only=True)
    isTopRated = serializers.BooleanField(source='is_top_rated', read_only=True)
    isFeatured = serializers.BooleanField(source='is_featured', read_only=True)
    profileUrl = serializers.CharField(source='profile_url', read_only=True)

    class Meta:
        model = Expert
        fields = [
            'id', 'userId', 'name', 'title', 'company', 'profileImageUrl',
            'hourlyRate', 'rating', 'reviewCount', 'totalHours', 'skills',
            'isAvailableSoon', 'isTopRated', 'isFeatured', 'profileUrl'
        ]


class ExpertDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Expert detail view with full profile information.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    profileImageUrl = serializers.CharField(source='profile_image_url', read_only=True)
    hourlyRate = serializers.DecimalField(source='hourly_rate', max_digits=6, decimal_places=2, read_only=True)
    reviewCount = serializers.IntegerField(read_only=True)
    totalMeetings = serializers.IntegerField(read_only=True)
    totalMeetingTime = serializers.CharField(read_only=True)
    isListed = serializers.BooleanField(source='is_listed', read_only=True)
    profileUrl = serializers.CharField(source='profile_url', read_only=True)
    companyLogo = serializers.URLField(source='company_logo', read_only=True)

    class Meta:
        model = Expert
        fields = [
            'id', 'name', 'title', 'company', 'bio', 'profileImageUrl',
            'hourlyRate', 'rating', 'reviewCount', 'totalMeetings',
            'totalMeetingTime', 'skills', 'isListed', 'profileUrl', 'companyLogo'
        ]


class ExpertProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Expert profile in user's own profile view.
    """
    id = serializers.CharField(read_only=True)
    hourlyRate = serializers.DecimalField(source='hourly_rate', max_digits=6, decimal_places=2, read_only=True)
    isListed = serializers.BooleanField(source='is_listed', read_only=True)
    profileUrl = serializers.CharField(source='profile_url', read_only=True)
    totalMeetings = serializers.IntegerField(read_only=True)
    totalMeetingTime = serializers.CharField(read_only=True)
    reviewCount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Expert
        fields = [
            'id', 'title', 'company', 'bio', 'hourlyRate', 'isListed',
            'profileUrl', 'totalMeetings', 'totalMeetingTime', 'rating', 'reviewCount'
        ]


class ExpertCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Expert listings.
    """
    hourlyRate = serializers.DecimalField(source='hourly_rate', max_digits=6, decimal_places=2)
    profileUrl = serializers.SlugField(source='profile_url', max_length=50)

    class Meta:
        model = Expert
        fields = ['title', 'company', 'bio', 'hourlyRate', 'skills', 'profileUrl']

    def validate_profileUrl(self, value):
        """Validate that profile URL is unique."""
        expert_id = self.instance.id if self.instance else None
        if Expert.objects.filter(profile_url=value).exclude(id=expert_id).exists():
            raise serializers.ValidationError("This profile URL is already taken.")
        return value

    def validate_skills(self, value):
        """Validate skills list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list.")
        
        valid_skills = [choice[0] for choice in Expert.SKILL_CHOICES]
        for skill in value:
            if skill not in valid_skills:
                raise serializers.ValidationError(f"'{skill}' is not a valid skill choice.")
        
        return value


class ExpertPublishSerializer(serializers.Serializer):
    """
    Serializer for publishing/unpublishing expert listings.
    """
    def update(self, instance, validated_data):
        """Publish the expert listing."""
        instance.publish_listing()
        return instance


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    """
    Serializer for individual availability time slots.
    """
    startTime = serializers.TimeField(source='start_time')
    endTime = serializers.TimeField(source='end_time')
    isAvailable = serializers.BooleanField(source='is_available', required=False, default=True)
    isEnabled = serializers.BooleanField(source='is_enabled', required=False, default=True)

    class Meta:
        model = Availability
        fields = ['startTime', 'endTime', 'isAvailable', 'isEnabled']


class DailyAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for daily availability schedule.
    """
    date = serializers.DateField()
    timeSlots = AvailabilitySlotSerializer(many=True)


class WeeklyDefaultsSerializer(serializers.Serializer):
    """
    Serializer for weekly default availability.
    """
    monday = AvailabilitySlotSerializer(many=True, required=False)
    tuesday = AvailabilitySlotSerializer(many=True, required=False)
    wednesday = AvailabilitySlotSerializer(many=True, required=False)
    thursday = AvailabilitySlotSerializer(many=True, required=False)
    friday = AvailabilitySlotSerializer(many=True, required=False)
    saturday = AvailabilitySlotSerializer(many=True, required=False)
    sunday = AvailabilitySlotSerializer(many=True, required=False)


class AvailabilitySerializer(serializers.Serializer):
    """
    Serializer for expert availability schedule.
    """
    timezone = serializers.CharField(max_length=50)
    schedule = DailyAvailabilitySerializer(many=True, required=False)
    weeklyDefaults = WeeklyDefaultsSerializer(required=False)


class AvailabilityUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating expert availability.
    """
    timezone = serializers.CharField(max_length=50)
    weeklyDefaults = WeeklyDefaultsSerializer(required=False)
    specificDates = DailyAvailabilitySerializer(many=True, required=False)


class BulkAvailabilityUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk updating availability for multiple dates.
    """
    dates = serializers.ListField(
        child=serializers.DateField(),
        min_length=1
    )
    timeSlots = AvailabilitySlotSerializer(many=True)
    timezone = serializers.CharField(max_length=50)


class ProfileLinkSerializer(serializers.Serializer):
    """
    Serializer for expert profile link information.
    """
    profileUrl = serializers.CharField(read_only=True)
    fullUrl = serializers.CharField(read_only=True)
    isPublic = serializers.BooleanField(read_only=True)


class ProfileUrlUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating expert profile URL.
    """
    profileUrl = serializers.SlugField(max_length=50)

    def validate_profileUrl(self, value):
        """Validate that profile URL is unique."""
        if Expert.objects.filter(profile_url=value).exists():
            raise serializers.ValidationError("This profile URL is already taken.")
        return value