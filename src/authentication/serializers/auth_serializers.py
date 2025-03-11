from rest_framework import serializers
from users.models import User

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer validates the provided user data (username, email, password, 
    and confirm_password), ensuring that the passwords match and the user can be 
    successfully created.

    Fields:
        username (str): The username of the user. Must be unique.
        email (str): The email address of the user. Must be unique.
        password (str): The password for the user. This is required for account creation.
        confirm_password (str): A confirmation password to ensure the user entered 
                                 the correct password.

    Methods:
        validate(attrs):
            Checks that the provided password and confirm_password match.

        create(validated_data):
            Creates a new user with the validated data, using the `create_user` method
            for proper password handling.
    """


    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password"]
        extra_kwargs = {
            "password":{"write_only": True}
        }

    def validate(self, data):
        """
        Validate the password and confirm_password fields.

        This method ensures that the password and the confirmation password match. 
        If they don't, it raises a validation error.

        Args:
            data (dict): A dictionary containing the user's input data, including 
                         'password' and 'confirm_password'.

        Returns:
            dict: The validated data, containing the user-provided fields.

        Raises:
            serializers.ValidationError: If the password and confirm_password do not match.
        """

        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        """
        Create a new user using the validated data.

        This method removes the 'confirm_password' field from the validated data 
        before passing it to the `create_user` method to create a new user. The 
        password is automatically hashed before being stored.

        Args:
            validated_data (dict): The data after validation, excluding 'confirm_password'.

        Returns:
            User: The newly created user object.

        Raises:
            IntegrityError: If the username or email already exists.
        """

        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        return user