from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import UserProfile, Experience, Career, Education, Review
from users.serializers.user_serializer import UserSerializer
from rest_framework.exceptions import ValidationError
from users.utils.user_profile_utils import calculate_average_rating
from django.core.files.images import get_image_dimensions
import pycountry


User = get_user_model()


class ExperienceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Experience model.

    Methods:
        - validate_weight(value): Ensures `weight` is a valid choice.
    
    Additional Fields:
        - weight_display: Returns the human-readable version of `weight`.
    """

    
    weight_display = serializers.CharField(source='get_weight_display', read_only=True)

    class Meta:
        model = Experience
        fields = ['id', 'name', 'weight', 'weight_display']
        read_only_fields = ['id']

    def validate_weight(self, value):
        """
        Validates that the weight is within the allowed choices.

        Args:
            value (str): The selected weight value.

        Raises:
            serializers.ValidationError: If the value is invalid.

        Returns:
            str: The validated weight value.
        """
        valid_choices = [choice[0] for choice in Experience.weight_choices]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Weight must be one of: {valid_choices}")
        return value
    
class CareerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Career model.

    Methods:
        - validate_job_status(value): Ensures `job_status` is a valid choice.
    """

    class Meta:
        model = Career
        fields = ['id', 'job_title', 'company_name', 'job_status', 'description', 'picture']
        read_only_fields = ['id']

    def validate_job_status(self, value):
        """
        Validates that `job_status` is a valid choice.

        Args:
            value (str): The job status provided by the user.

        Raises:
            serializers.ValidationError: If the value is not valid.

        Returns:
            str: The validated job status.
        """
        valid_choices = [choice[0] for choice in Career._meta.get_field('job_status').choices]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Job status must be one of: {valid_choices}")
        return value
    
class EducationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Education model.

    Meta:
        - model: Education
        - fields: Includes 'id', 'school_name', 'diploma', 'description', 'picture'
        - read_only_fields: 'id'
    """
    picture = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Education
        fields = ['id', 'school_name', 'diploma', 'description', 'picture', 'user_profile']
        read_only_fields = ['id']

    def validate_picture(self, value):
        """
        Validates the uploaded picture.
        
        Args:
            value (UploadedFile): The uploaded image file.

        Raises:
            serializers.ValidationError: If the file is not a valid image, exceeds size limits,
            or has invalid dimensions.

        Returns:
            UploadedFile: The validated profile picture.
        
        """
        if value is None:
            return value
        
        max_size = 5 * 1024 * 1024
        allowed_formats = ['image/jpeg',"image/png"]

        if value.size > max_size:
            raise serializers.ValidationError("Picture must be less than 5MB.")
        if value.content_type not in allowed_formats:
            raise serializers.ValidationError("Only JPEG and PNG formats are allowed.")
        
        width, height = get_image_dimensions(value)
        if width > 4000 or height > 4000:
            raise serializers.ValidationError("Image dimensions must not exceed 4000x4000 pixels.")
        
        return value



class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.

    Methods:
        - validate_rating(value): Ensures the rating is within 0-10.

    Additional Fields:
        - reviewer_info: Includes reviewer details using `UserSerializer`.
    """

    reviewer_info = UserSerializer(source='reviewer', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'reviewer', 'reviewer_info']
        read_only_fields = ['id', 'reviewer_info']

    def validate_rating(self, value):
        """
        Ensures the rating is between 0 and 10.

        Args:
            value (int): The rating value.

        Raises:
            serializers.ValidationError: If the rating is out of bounds.

        Returns:
            int: The validated rating value.
        """
        if value < 0 or value > 10:
            raise serializers.ValidationError("Rating must be between 0 and 10.")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model.

    Methods:
        - get_average_rating(obj): Computes the average rating for a user profile.

    Related Models:
        - Includes nested serializers for Experience, Career, Education, and Reviews.

    Additional Fields:
        - average_rating: Dynamically calculates the user's average rating.
    """

    user = UserSerializer(read_only = True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    careers = CareerSerializer(many=True,read_only = True)
    educations = EducationSerializer(many=True,read_only = True)
    reviews = ReviewSerializer(many=True,read_only = True)
    average_rating = serializers.SerializerMethodField(read_only = True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'profile_picture', 'country', 'job_title', 'company_name',
            'total_meetings', 'meetings_completed', 'total_minutes', 'rating',
            'description', 'experiences', 'careers', 'educations', 'reviews',
            'average_rating'
        ]
        read_only_fields = ['id', 'total_meetings', 'meetings_completed', 'total_minutes', 'rating']


    def get_average_rating(self, obj):
        """
        Computes the average rating for the user profile.

        Args:
            obj (UserProfile): The user profile instance.

        Returns:
            float: The computed average rating or 0 if no reviews exist.
        """
        return calculate_average_rating(obj.reviews.all())
        
    

class UserProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating a UserProfile.

    Methods:
        - validate_country(value): Ensures the country name is at least 2 characters long.

    Field Behavior:
        - profile_picture: Write-only to allow uploads without exposing data.
    """

    profile_picture = serializers.ImageField(write_only=True) # Prevents returning image in responses
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'country', 'job_title', 'company_name', 'description'
        ]
    def validate_country(self, value):
        """
        Ensures the country name is at least 2 characters long.

        Args:
            value (str): The country name.

        Raises:
            serializers.ValidationError: If the country name is too short.

        Returns:
            str: The validated country name.
        """
        if len(value) < 2:
            raise serializers.ValidationError("Country name is too short.")
        
        valid_countries = [country.name for country in pycountry.countries]
        if value not in valid_countries:
            raise serializers.ValidationError("Invalid country name.")
        
        return value
    
    def validate_profile_picture(self, value):
        """
        Validates the uploaded profile picture.
        
        Args:
            value (UploadedFile): The uploaded image file.

        Raises:
            serializers.ValidationError: If the file is not a valid image, exceeds size limits,
            or has invalid dimensions.

        Returns:
            UploadedFile: The validated profile picture.
        
        """
        max_size = 5 * 1024 * 1024
        allowed_formats = ['image/jpeg',"image/png"]

        if value.size > max_size:
            raise serializers.ValidationError("Profile picture must be less than 5MB.")
        if value.content_type not in allowed_formats:
            raise serializers.ValidationError("Only JPEG and PNG formats are allowed.")
        
        width, height = get_image_dimensions(value)
        if width > 4000 or height > 4000:
            raise serializers.ValidationError("Image dimensions must not exceed 4000x4000 pixels.")
        
        return value
