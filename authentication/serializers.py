from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import RefreshToken as CustomRefreshToken, LinkedInProfile
from users.serializers import UserSerializer

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Validate email and password."""
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Must include email and password.")

        return data


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response data.
    """
    accessToken = serializers.CharField(read_only=True)
    refreshToken = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'password', 'firstName', 'lastName', 'country']
        extra_kwargs = {
            'country': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        """Validate that email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        # Only mark profile complete if all required fields are provided
        # Since first_name, last_name, and country are now optional during registration,
        # profile completion will be handled later in the application flow
        user.mark_profile_complete()
        return user


class RegisterResponseSerializer(serializers.Serializer):
    """
    Serializer for registration response data.
    """
    user = UserSerializer(read_only=True)
    requiresEmailVerification = serializers.BooleanField(read_only=True)


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    email = serializers.EmailField(required=True)
    verificationCode = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate(self, data):
        """Validate email and verification code."""
        from users.models import EmailVerification
        
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


class EmailVerificationResponseSerializer(serializers.Serializer):
    """
    Serializer for email verification response data.
    """
    message = serializers.CharField(read_only=True)
    accessToken = serializers.CharField(read_only=True)
    refreshToken = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


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


class LinkedInAuthSerializer(serializers.Serializer):
    """
    Serializer for LinkedIn OAuth authentication.
    """
    code = serializers.CharField(required=True)
    redirectUri = serializers.URLField(required=True)

    def validate(self, data):
        """Validate LinkedIn OAuth code and exchange for user data."""
        # In a real implementation, this would:
        # 1. Exchange the code for an access token with LinkedIn
        # 2. Fetch user profile data from LinkedIn API
        # 3. Create or update user account
        
        # For now, we'll simulate this process
        # This would be replaced with actual LinkedIn API integration
        
        # Simulated LinkedIn user data
        linkedin_data = {
            'id': 'linkedin_user_123',
            'email': 'user@example.com',
            'firstName': 'John',
            'lastName': 'Doe',
            'profilePicture': 'https://linkedin.com/profile.jpg'
        }
        
        data['linkedin_data'] = linkedin_data
        return data


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for refreshing JWT tokens.
    """
    refreshToken = serializers.CharField(required=True)

    def validate_refreshToken(self, value):
        """Validate refresh token."""
        try:
            token = CustomRefreshToken.objects.get(token=value)
        except CustomRefreshToken.DoesNotExist:
            raise serializers.ValidationError("Invalid refresh token.")

        if not token.is_valid():
            raise serializers.ValidationError("Refresh token has expired or been revoked.")

        return value


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.
    """
    refreshToken = serializers.CharField(required=False)

    def validate(self, data):
        """Validate and revoke refresh token if provided."""
        refresh_token = data.get('refreshToken')
        
        if refresh_token:
            try:
                token = CustomRefreshToken.objects.get(token=refresh_token)
                token.revoke()
            except CustomRefreshToken.DoesNotExist:
                # Token doesn't exist, but we don't want to reveal this
                pass
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate that user exists."""
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            # Don't reveal whether the email exists or not
            return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, validators=[validate_password])

    def validate_token(self, value):
        """Validate password reset token."""
        from .models import PasswordResetToken
        
        try:
            token = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")

        if not token.is_valid():
            raise serializers.ValidationError("Reset token has expired or been used.")

        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    currentPassword = serializers.CharField(required=True, write_only=True)
    newPassword = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate_currentPassword(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value