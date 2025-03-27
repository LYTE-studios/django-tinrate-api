from calendar import Day
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from users.models.profile_models import UserProfile, Experience
from listings.models.listings_models import Listing, Day, Availability, Meeting
from listings.utils.listings_utils import minutes_to_hours


class ListingSerializer(serializers.ModelSerializer):
    """
    A serializer for the Listing model. This serializer handles the validation, 
    serialization, and deserialization of Listing data, including user profile 
    information, listing details, and calculated fields like total reviews and total hours.

    Methods:
        - validate_completion: Ensures that required fields are filled before marking a listing as complete.
        - validate_availability: Ensures the availability JSON structure is valid.
        - get_rating: Retrieves the user's rating from their profile.
        - get_total_reviews: Retrieves the total number of reviews (not implemented in this example).
        - get_total_hours: Converts the user's total minutes to hours and returns it.
    """

    first_name = serializers.CharField(source="user_profile.user.first_name", read_only=True)
    last_name = serializers.CharField(source="user_profile.user.last_name", read_only=True)
    country = serializers.CharField(source="user_profile.country", read_only=True)
    profile_picture = serializers.ImageField(source="user_profile.profile_picture", read_only=True)
    job_title = serializers.CharField(source="user_profile.job_title", read_only=True)
    company_name = serializers.CharField(source="user_profile.company_name", read_only=True)
    rating = serializers.CharField(source="user_profile.rating", read_only=True)
    
    # Experience-related fields
    experience_name = serializers.CharField(source="experience.name", read_only=True)
    
    total_reviews = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()
    availability = serializers.JSONField()  
    availabilities = AvailabilitySerializer(many=True, read_only=True) 
    

    class Meta:
        model = Listing
        fields = ['id', 'first_name', 'last_name', 'country', 'profile_picture', 'job_title', 'company_name', 
          'experience_name', 'pricing_per_hour', 'service_description', 'availability', 'availabilities', 'completion_status', 
          'rating', 'total_reviews', 'total_hours', 'user_profile']

        read_only_fields = ['first_name', 'last_name', 'country', 'profile_picture', 'job_title', 'company_name', 
            'experience_name', 'rating', 'total_reviews', 'total_hours']
        
    def validate_completion(self, data):
        """
        Validate the completion status of the listing. Ensures that all required fields are completed 
        before setting the completion status to True.

        If `completion_status` is set to True, the serializer checks if all required fields have been 
        provided. If any fields are missing, a validation error is raised. If no required fields are 
        missing and the listing is marked as incomplete, the completion status is automatically set to True.

        Args:
            data (dict): The validated data for the listing.

        Returns:
            dict: The validated and possibly modified data, with completion status updated.

        Raises:
            serializers.ValidationError: If required fields are missing when attempting to mark the listing as complete.
        """

        required_fields = ['pricing_per_hour','service_description', 'job_title', 'company_name', 'experience_name', 'availability']

        if data.get('completion_status', False):
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Cannot mark as complete. Missing fields: {', '.join(missing_fields)}"
                )
        else:
            missing_fields = [field for field in required_fields if not data.get(field)]
            if not missing_fields:
                data['completion_status'] = True
        return data
        
    def validate_availability(self, value):
        """
        Validate the availability field, ensuring it is a dictionary with the required keys.

        Args:
            value (dict): The availability JSON structure containing days, start_time, and end_time.

        Returns:
            dict: The validated availability data.

        Raises:
            serializers.ValidationError: If the availability is not a dictionary or if any required keys are missing.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Availability must be a dictionnary.")

        required_keys = ['days', 'start_time', 'end_time']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"{key} is required in availability.")
        return value
    
    def get_rating(self, obj):
        """
        Retrieve the rating from the user's profile.

        Args:
            obj (Listing): The listing instance.

        Returns:
            str: The user's rating if available, otherwise None.
        """
        return obj.user_profile.rating if obj.user_profile else None

    def get_total_reviews(self, obj):
        """
        Calculate and return the total number of reviews for the listing.
        
        Args:
            obj (Listing): The listing instance.

        Returns:
            int: The total number of reviews for the listing.
        """
        return obj.user_profile.reviews.count()

    def get_total_hours(self, obj):
        """
        Calculate and return the total hours worked, based on the user's total minutes.

        Args:
            obj (Listing): The listing instance.

        Returns:
            float: The total hours worked (converted from minutes).
        """
        return minutes_to_hours(obj.user_profile.total_minutes) if obj.user_profile else None
    

class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = ['id', 'day_of_week', 'is_available', 'start_time', 'end_time']


class AvailabilitySerializer(serializers.ModelSerializer):
    monday = DaySerializer(required=False)
    tuesday = DaySerializer(required=False)
    wednesday = DaySerializer(required=False)
    thursday = DaySerializer(required=False)
    friday = DaySerializer(required=False)
    saturday = DaySerializer(required=False)
    sunday = DaySerializer(required=False)

    class Meta:
        model = Availability
        fields = ['id', 'listing', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']