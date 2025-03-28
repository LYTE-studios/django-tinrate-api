from calendar import Day
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from users.models.profile_models import UserProfile, Experience
from listings.models.listings_models import Listing, Day, Availability, Meeting
from listings.utils.listings_utils import minutes_to_hours
from django.utils import timezone


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

    class Meta:
        model = Listing
        fields = ['id', 'first_name', 'last_name', 'country', 'profile_picture', 'job_title', 'company_name', 
          'experience_name', 'pricing_per_hour', 'service_description', 'availability', 'completion_status', 
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
    """
    Serializer for the Day model.

    This serializer handles:
    - Retrieving and updating the availability of a specific day.
    - Ensuring that time constraints are met when a day is marked as available.

    Fields:
        - id (int, read-only): Unique identifier for the day.
        - day_of_week (str, read-only): The name of the day (Monday, Tuesday, etc.).
        - is_available (bool): Whether the expert is available on this day.
        - start_time (time, optional): The start time of availability (if applicable).
        - end_time (time, optional): The end time of availability (if applicable).

    Validation:
        - If `is_available` is `True`, both `start_time` and `end_time` must be provided.
        - `start_time` must be earlier than `end_time`.
    """

    class Meta:
        model = Day
        fields = ['id', 'day_of_week', 'is_available', 'start_time', 'end_time']
        read_only_fields = ['id', 'day_of_week']

    def validate(self, data):
        """
        Validate the time constraints when a day is marked as available.

        Raises:
            serializers.ValidationError: If `start_time` and `end_time` are missing 
            when `is_available` is `True`, or if `start_time` is later than `end_time`.
        """
        is_available = data.get('is_available', False)
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if is_available:
            if not start_time or not end_time:
                raise serializers.ValidationError({
                    'time':'Both start_time and end_time are required when availability is True'
                })
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'time':'Start time must be before end time.'
                })
        return data


class AvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for the Availability model.

    This serializer is responsible for:
    - Handling the validation and creation of availability entries.
    - Ensuring that at least one day of the week has availability set to True.
    - Preventing duplicate availability entries for the same listing.

    Fields:
        - id (int, read-only): Unique identifier for the availability record.
        - listing (ForeignKey, read-only): The listing associated with this availability.
        - monday-sunday (nested `DaySerializer`): Availability data for each day of the week.

    Methods:
        - validate: Ensures at least one day is marked as available.
        - validate_listing: Ensures no duplicate availability exists for the listing.
    """
    
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
        read_only_fields = ['id', 'listing']

    def validate_listing(self, listing):
        """
        Validates that there is no existing availability entry for the provided listing.

        If an availability entry already exists for the listing, a validation error is raised.

        Args:
            listing (Listing): The listing object for which availability is being created.

        Raises:
            serializers.ValidationError: If an availability entry already exists for the listing.
        """

        existing_availabilities = Availability.objects.filter(listing=listing)
        if existing_availabilities.exists():
            raise serializers.ValidationError(
                'An availability entry already exists for this listing.'
            )
        return listing


    def create(self, validated_data):
        """
        Create a new Availability instance and associated Day instances.

        This method creates an Availability object from the provided validated data.
        It then iterates over each day of the week ('monday' through 'sunday') and 
        creates a Day object for each day where data is provided. Each Day is linked
        to the created Availability object.

        Args:
            validated_data (dict): The validated data passed to the serializer,
                                    including fields for the availability as well
                                    as any day-specific data (e.g., 'monday', 'tuesday', etc.).

        Returns:
            Availability: The newly created Availability instance.
        """
        day_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        days_data = {field: validated_data.pop(field, None) for field in day_fields}
        
    
        availability = Availability.objects.create(**validated_data)
        

        for day_name, day_data in days_data.items():
            if day_data:
                day_obj, _ = Day.objects.get_or_create(
                    day_of_week=day_name,
                    defaults={
                        'is_available': day_data.get('is_available', False),
                        'start_time': day_data.get('start_time'),
                        'end_time': day_data.get('end_time')
                    }
                )
                setattr(availability, day_name, day_obj)
                
        availability.save()
        return availability
    
    def update(self, instance, validated_data):
        """
        Update an existing Availability instance and its associated Day instances.

        This method updates the fields of an existing Availability object with the
        provided validated data. It also updates or creates Day objects for each
        day of the week ('monday' through 'sunday') if corresponding data is provided.
        Each updated or newly created Day object is linked to the updated Availability
        instance.

        Args:
            instance (Availability): The existing Availability instance to update.
            validated_data (dict): The validated data passed to the serializer,
                                    which may include fields for the availability and
                                    data for specific days of the week.

        Returns:
            Availability: The updated Availability instance.
        """
        day_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        days_data = {field: validated_data.pop(field, None) for field in day_fields}

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        for day_name, day_data in days_data.items():
            if day_data:
                # Remove the 'availability=instance' parameter
                day_obj, created = Day.objects.get_or_create(day_of_week=day_name)
                
                # Link the day to the availability instance if needed
                day_obj.availability = instance
                
                for key, value in day_data.items():
                    setattr(day_obj, key, value)
                day_obj.save()
        
        return instance

    
    def validate(self, data):
        """
        Validates the availability data to ensure that at least one day is available.

        If no days are marked as available (i.e., no day has `is_available` set to True),
        a validation error is raised.

        Args:
            data (dict): The incoming validated data for the Availability model.

        Raises:
            serializers.ValidationError: If no day is marked as available.
        """

        available_days = [
            'monday', 'tuesday', 'wednesday', 
            'thursday', 'friday', 'saturday', 'sunday'
        ]

        days_with_availability = [
            day for day in available_days
            if data.get(day) and data[day].get('is_available', False)
        ]

        if not days_with_availability:
            raise serializers.ValidationError({
                'availability':'At least one day must be available.'
            })
        return data
    
    