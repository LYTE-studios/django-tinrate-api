from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from users.models import (
    UserProfile,
    NotificationPreferences,
    PaymentSettings,
    SupportTicket,
)

User = get_user_model()

class ProfileSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile settings.
    
    Attributes:
        first_name (CharField): First name of the user, sourced from the related User model.
        last_name (CharField): Last name of the user, sourced from the related User model.
    
    Methods:
        update(instance, validated_data):
            Updates the user's profile settings, including handling nested user data updates.
    """
    first_name = serializers.CharField(source='user.fist_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model: UserProfile
        fields = ['profile_picture', 'first_name', 'last_name', 'description']

    def update(self, instance, validated_data):
        """
        Updates the user profile settings.
        
        If user-related data is provided, it updates the corresponding user fields.
        Then, it updates the UserProfile instance with the remaining validated data.
        
        Args:
            instance (UserProfile): The current instance of the user profile.
            validated_data (dict): The validated data to update the instance.
        
        Returns:
            UserProfile: The updated user profile instance.
        """
        user_data = validated_data.pop('user', None)

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        return super().update(instance, validated_data)
    

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for handling password change requests.
    
    Attributes:
        old_password (CharField): The user's current password.
        new_password1 (CharField): The new password the user wants to set.
        new_password2 (CharField): Confirmation of the new password.

     Methods:
        validate_old_password(value): Ensures the old password is correct.
        validate(data): Validates the new password fields and applies Django's password validation rules.
        save(): Updates the user's password in the database.
    """
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password1 = serializers.CharField(style={'input_type': 'password'})
    new_password2 = serializers.CharField(style={'input_type': 'password'})

    def validate_old_password(self, value):
        """
        Validates whether the provided old password matches the user's current password.
        
        Args:
            value (str): The old password entered by the user.
        
        Raises:
            serializers.ValidationError: If the old password is incorrect.
        
        Returns:
            str: The validated old password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Your old password is incorrect.')
        return value
    
    def validate(self, data):
        """
        Validates whether the new passwords match and meet security requirements.
        
        Args:
            data (dict): The validated data containing password fields.
        
        Raises:
            serializers.ValidationError: If the new passwords do not match or do not meet security requirements.
        
        Returns:
            dict: The validated password data.
        """
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields do not match."})
        
        user = self.context['request'].user
        try:
            password_validation.validate_password(data['new_password1'], user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password1": list(e.messages)})
        return data
    
    def save(self):
        """
        Saves the new password for the user.
        
        Returns:
            User: The updated user instance with the new password set.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for managing user notification preferences.
    
    This serializer allows users to customize their notification settings.
    
    Methods:
        validate_preferred_method(value): Ensures the chosen notification method is valid.
    """
    class Meta:
        model: NotificationPreferences
        fields = [
            'booking_notifications',
            'payment_notifications',
            'meeting_reminders',
            'updates_promotions',
            'preferred_method',
        ]
    
    def validate_preferred_method(self, value):
        """
        Validates that the preferred notification method is one of the allowed choices.
        
        Args:
            value (str): The selected preferred notification method.
        
        Raises:
            serializers.ValidationError: If the selected method is not valid.
        
        Returns:
            str: The validated preferred notification method.
        """
        valid_choices = [choice[0] for choice in NotificationPreferences.NOTIFICATION_METHODS]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Method must be one of: {valid_choices}")
        return value
    
class PaymentSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for managing user payment settings.
    
    This serializer ensures that payment details are correctly validated based on the selected method.
    
    Methods:
        validate(data): Ensures required fields are provided based on the chosen payment method.
    """
    class Meta:
        model: PaymentSettings
        fields = [
            'payment_method',
            'allow_cancellation_fee',
            'paypal_email',
            'bank_account_name',
            'bank_account_number',
            'bank_name',
            'crypto_wallet_address',
        ]

    def validate(self, data):
        """
        Validate that required fields are provided based on the payment method.
        
        Args:
            data (dict): The payment settings data.
        
        Raises:
            serializers.ValidationError: If required fields are missing for the chosen payment method.
        
        Returns:
            dict: The validated payment settings data.
        """
        payment_method = data.get('payment_method')

        if payment_method == 'paypal' and not data.get('paypal_email'):
            raise serializers.ValidationError({"paypal_email": "PayPal email is required when using PayPal."})
        
        if payment_method == 'bank_transfer':
            if not data.get('bank_account_name'):
                raise serializers.ValidationError({"bank_account_name": "Account name is required for bank transfers."})
            if not data.get('bank_account_number'):
                raise serializers.ValidationError({"bank_account_number": "Account number is required for bank transfers."})
            if not data.get('bank_name'):
                raise serializers.ValidationError({"bank_name": "Bank name is required for bank transfers."})
        
        if payment_method == 'crypto' and not data.get('crypto_wallet_address'):
            raise serializers.ValidationError({"crypto_wallet_address": "Wallet address is required for cryptocurrency payments."})
        
        return data

class SupportTicketSerializer(serializers.ModelSerializer):
    """
    Serializer for the SupportTicket model, which is used to validate and
    serialize data for creating and updating support tickets.

    Fields:
        - issue_type: The type of the issue reported by the user.
        - description: A detailed description of the issue.
        - created_at: The timestamp when the support ticket was created (read-only).
        - resolved: A flag indicating whether the support ticket has been resolved (read-only).
        - resolution_notes: Any notes related to the resolution of the ticket (read-only).

    Methods:
        - validate_issue_type: Validates the issue_type field to ensure it is one of the predefined valid issue types.
    """
    class Meta:
        model = SupportTicket
        fields = ['issue_type', 'description']
        read_only_fields = ['created_at', 'resolved', 'resolution_notes']

    def validate_issue_type(self, value):
        """
        Validates that the provided issue_type is a valid choice from the 
        predefined list of valid issue types.

        Args:
            value (str): The issue type value to validate.

        Returns:
            str: The validated issue type.

        Raises:
            serializers.ValidationError: If the issue type is not valid.
        """
        valid_choices = [choice[0] for choice in SupportTicket.ISSUE_TYPES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Issue type must be one of: {valid_choices}")
        return value

        