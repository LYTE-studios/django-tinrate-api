from rest_framework import serializers
from users.models import User
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer validates the provided user data (email, password, 
    and confirm_password), ensuring that the passwords match and the user can be 
    successfully created. Ensures that email is used as username.

    Fields:
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
        fields = ["email", "password", "confirm_password"]
        extra_kwargs = {
            "password":{"write_only": True},
            "username": {"validators": []}
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

    def validate_email(self, value):
        """
        Validate the email field.

        This method checks if the provided email address is already registered. 
        If the email exists in the database, it raises a validation error.

        Args:
            value (str): The email address provided by the user.

        Returns:
            str: The validated email address if it does not already exist.

        Raises:
            serializers.ValidationError: If the email is already registered.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
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
        user = User.objects.create_user(username=validated_data["email"], **validated_data)
        return user
    

class LoginSerializer(serializers.ModelSerializer):
    """
    Serializer for user login.

    This serializer validates the provided user credentials (email or username 
    and password). If valid, it returns authentication tokens (access & refresh).

    Fields:
        username (str): The username or email of the user.
        password (str): The password for authentication.

    Methods:
        validate(attrs):
            - Authenticates the user using Django's `authenticate` method.
            - If authentication fails, raises a validation error.
            - If authentication is successful, returns the authenticated user.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password"]
        extra_kwargs = {
            "password":{"write_only": True},
        }

    
    def validate(self, attrs):
        """
        Validate user credentials.

        This method uses Django's `authenticate()` function to check if 
        the provided username and password are correct. If authentication 
        fails, it raises a validation error.

        Args:
            attrs (dict): The input data containing username and password.

        Returns:
            dict: A dictionary containing the authenticated user.

        Raises:
            serializers.ValidationError: If authentication fails.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        if not User.objects.filter(email=email).exists():
         raise serializers.ValidationError({"email": "This email is not registered."})

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials. Please try again.")
      
        
        attrs["user"] = user
        return attrs
    
   
       
        
