from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailVerification

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model that matches the TinRate API specification.
    """
    id = serializers.CharField(read_only=True)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    profileImageUrl = serializers.URLField(source='profile_image_url', required=False, allow_null=True)
    isEmailVerified = serializers.BooleanField(source='is_email_verified', read_only=True)
    profileComplete = serializers.BooleanField(source='profile_complete', read_only=True)
    isExpert = serializers.BooleanField(source='is_expert', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'lastName', 'country',
            'profileImageUrl', 'isEmailVerified', 'profileComplete',
            'isExpert', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'email', 'isEmailVerified', 'profileComplete', 'isExpert', 'createdAt', 'updatedAt']

    def update(self, instance, validated_data):
        """Update user instance and check if profile is complete."""
        instance = super().update(instance, validated_data)
        instance.mark_profile_complete()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    firstName = serializers.CharField(source='first_name', required=True)
    lastName = serializers.CharField(source='last_name', required=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'firstName', 'lastName', 'country']

    def validate_email(self, value):
        """Validate that email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        user.mark_profile_complete()
        return user


class UserProfileCompleteSerializer(serializers.Serializer):
    """
    Serializer for completing user profile.
    """
    firstName = serializers.CharField(required=True)
    lastName = serializers.CharField(required=True)
    country = serializers.CharField(required=True, max_length=2)

    def update(self, instance, validated_data):
        """Update user profile and mark as complete."""
        instance.first_name = validated_data['firstName']
        instance.last_name = validated_data['lastName']
        instance.country = validated_data['country']
        instance.profile_complete = True
        instance.save()
        return instance


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    email = serializers.EmailField(required=True)
    verificationCode = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate(self, data):
        """Validate email and verification code."""
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        try:
            verification = EmailVerification.objects.filter(
                user=user,
                verification_code=data['verificationCode'],
                is_used=False
            ).latest('created_at')
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code.")

        if not verification.is_valid():
            raise serializers.ValidationError("Verification code has expired or been used.")

        data['user'] = user
        data['verification'] = verification
        return data


class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending email verification.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate that user exists and is not already verified."""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.is_email_verified:
            raise serializers.ValidationError("Email is already verified.")

        return value


class UserWithExpertProfileSerializer(UserSerializer):
    """
    Serializer for User with Expert Profile information.
    """
    expertProfile = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['expertProfile']

    def get_expertProfile(self, obj):
        """Get expert profile if user is an expert."""
        if hasattr(obj, 'expert_profile'):
            from experts.serializers import ExpertProfileSerializer
            return ExpertProfileSerializer(obj.expert_profile).data
        return None