from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.models.user_models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user information. It handles validation, updating, and deleting 
    user information.

    Methods:
        validate_username: Checks if the username already exists.
        validate_email: Checks if the email already exists.
        validate_name_fields: Ensures first name and last name are non-empty if provided.
        update_user: Updates the user information.
        delete_user: Deletes the user account.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

    def validate_username(self, value):
        """Validates that the username is unique and not already taken."""
        instance = getattr(self, 'instance', None)
        if User.objects.filter(username=value).exclude(pk=instance.pk if instance else None).exists():
            raise ValidationError("This username is already taken.")
        return value
    
    def validate_email(self, value):
        """Validates that the email is unique and not already taken."""
        instance = getattr(self, 'instance', None)
        if User.objects.filter(email=value).exclude(pk=instance.pk if instance else None).exists():
            raise ValidationError("This email is already taken.")
        return value
    
    def validate_name_fields(self, data):
        """Validates the first and last name fields to ensure they are not empty if provided."""
        if 'first_name' in data and not data['first_name'].strip():
            raise ValidationError({"first_name": "First name cannot be empty if provided."})
        if 'last_name' in data and not data['last_name'].strip():
            raise ValidationError({"last_name": "Last name cannot be empty if provided."})
        return data
    
    def update_user(self, instance, validated_data):
        """Updates the user information, excluding the password and other sensitive information."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete_user(self, instance):
        """Deletes the user account."""
        instance.delete()
        return ({"message": "User account deleted successfully."})        



