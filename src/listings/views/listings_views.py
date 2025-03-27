from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from rest_framework import status
from listings.serializers.listings_serializers import ListingSerializer, DaySerializer, AvailabilitySerializer
from listings.models.listings_models import Listing, Day, Availability, Meeting
from users.models.profile_models import UserProfile
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import models
from django.db.models import Q
from listings.permissions import ReadOnlyOrAuthenticatedEdit



class ListingViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing listings. Handles CRUD operations such as 
    creating, retrieving, updating, and deleting listings. Additionally, 
    the viewset filters listings based on completion status and user profile.

    Permissions:
        Only authenticated users can access this viewset.
    """
    serializer_class = ListingSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:  # Allow unauthenticated for GET actions
            return [AllowAny()]
        return [IsAuthenticated()]  

    def get_queryset(self):
        """
        Returns the queryset of listings. Filters listings to show only those that are:
        - Completed listings (`completion_status=True`) or
        - Belong to the current authenticated user (`user_profile__user=user`).

        Returns:
            queryset (QuerySet): Filtered listings visible to the current user.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Listing.objects.filter(completion_status=True)

        user = self.request.user
        return Listing.objects.filter(Q(completion_status=True) | Q(user_profile__user=user))
    
    def get_object(self):
        """
        Retrieve and validate access to a specific listing.
        
        Returns:
            Listing: The requested listing if the user has permission
        
        Raises:
            PermissionDenied: If the user doesn't have access to the listing
            Http404: If the listing doesn't exist
        """
        obj = get_object_or_404(Listing, pk=self.kwargs['pk'])

        if obj.completion_status:
            return obj
        
        # Check if the current user owns the listing
        if obj.user_profile.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this listing.")
        
        return obj
    
    def create(self, request, *args, **kwargs):
        """
        Create a new listing for the current authenticated user. The user profile is retrieved 
        to associate the listing. If the user profile is not found, a 400 response is returned.

        Args:
            request (Request): The request object containing the listing data

        Returns:
            Response: The created listing data along with a 201 status code on success
        """
    
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {'error':'User profile not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing = serializer.save(
            user_profile=user_profile,
            completion_status=False
        )
        return Response(
            self.get_serializer(listing).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing listing. This allows partial updates for the listing fields. 
        The user must own the listing to update it.

        Args:
            request (Request): The request object containing the updated data
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: The updated listing data
        """
        
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a listing. The user must own the listing to delete it.

        Args:
            request (Request): The request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: A response indicating successful deletion (204 status code)
        """
        
        instance = self.get_object()

        if instance.user_profile.user != request.user:
            raise PermissionDenied("You do not have permission to delete this listing.")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        """
        List all listings visible to the current user. Users can filter listings 
        based on `country` and `experience` query parameters.

        Args:
            request (Request): The request object containing filter parameters (optional)

        Returns:
            Response: A list of listings matching the filters provided
        """
        
        queryset = self.filter_queryset(self.get_queryset())
        country = request.query_params.get('country')
        experience = request.query_params.get('experience')

        filters = { "user_profile__country": country, "experience__name": experience }
        filters = {k: v for k, v in filters.items() if v}  # Remove None values
        queryset = queryset.filter(**filters)


        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific listing. If the listing is not completed, only the owner can access it.

        Args:
            request (Request): The request object containing the listing ID
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: The requested listing data
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    


class DayViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing individual days within a user's availability.

    This viewset allows authenticated users to:
    - Retrieve their availability days (`GET`).
    - Toggle availability on/off for a given day (`PATCH`).
    - Users cannot manually create or delete days, as all seven days exist by default.

    Restrictions:
    - Users can only view or modify days associated with their own listings.
    - Prevents unauthorized modifications to other users' availability schedules.
    """
    
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    permission_classes = [ReadOnlyOrAuthenticatedEdit]

    def get_queryset(self):
        """
        Retrieve all seven days for each availability associated with the user's listings.

        Returns:
            QuerySet: Days related to the authenticated user's availabilities.
        """
        listing_id = self.request.query_params.get('listing', None)

        if not listing_id:
            return Day.objects.none()
        
        try:
            listing = Listing.objects.get(
                id=listing_id, 
            )
            
            availability = listing.availability
            
    
            available_days = []
            day_fields = [
                'monday', 'tuesday', 'wednesday', 'thursday', 
                'friday', 'saturday', 'sunday'
            ]
            
            for day_field in day_fields:
                day = getattr(availability, day_field, None)
                if day and day.is_available:
                    available_days.append(day)
            
            return Day.objects.filter(id__in=[day.id for day in available_days])
        
        except Listing.DoesNotExist:
            return Day.objects.none()
        
    def partial_update(self, request, *args, **kwargs):
        """
        Override the default partial update behavior.
        """
        return super().partial_update(request, *args, **kwargs)


    def perform_update(self, serializer):
        """
        Toggle the availability status for an existing day.

        Raises:
            PermissionDenied: If the user does not own the listing.

        Args:
            serializer (DaySerializer): The serializer instance containing updated day data.

        Returns:
            Day: The updated day instance.
        """
        day = self.get_object()

        availability = Availability.objects.filter(
            models.Q(monday=day) | models.Q(tuesday=day) |
            models.Q(wednesday=day) | models.Q(thursday=day) |
            models.Q(friday=day) | models.Q(saturday=day) |
            models.Q(sunday=day)
        ).first() 


        if not availability or not availability.listing:
            raise PermissionDenied("This day is not associated with any listing.")

        listing_owner = availability.listing.user_profile.user

        if self.request.user != listing_owner:
            raise PermissionDenied("You do not have permission to update this day.")

        serializer.save()
            


        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def create(self, request, *args, **kwargs):
        """ Prevent users from creating new Day instances manually. """
        raise MethodNotAllowed("POST method is not allowed for this endpoint.")


class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing availability settings for a listing.

    This viewset allows authenticated users to:
    - Retrieve their availabilities (`GET`).
    - Create availability for a listing they own (`POST`).
    - Update availability settings (`PUT`, `PATCH`).
    - Prevent unauthorized modifications to listings owned by other users.

    Restrictions:
    - Users can only view or modify availabilities associated with their own listings.
    - Once an availability is created, its associated listing cannot be changed.
    """

    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve availabilities for the authenticated user's listings.

        Returns:
            QuerySet: Availability objects linked to the user's listings.
        """
        listing_id=self.request.query_params.get('listing', None)

        if listing_id:
            try:
                Listing.objects.get(
                    id=listing_id,
                    user_profile__user=self.request.user
                )
                return Availability.objects.filter(
                    listing_id=listing_id
                )
            except Listing.DoesNotExist:
                return Availability.objects.none()
        
        return Availability.objects.filter(listing__user_profile__user=self.request.user)
    
    def create(self, request):
        """
        Create an availability entry for a listing owned by the authenticated user.

        Raises:
            HTTP_400_BAD_REQUEST: If no listing ID is provided.
            HTTP_404_NOT_FOUND: If the listing does not exist.
            HTTP_403_FORBIDDEN: If the user does not own the listing.

        Args:
            request (Request): The HTTP request containing availability data.

        Returns:
            Response: Created availability data or an error message.
        """

        listing_id = request.data.get('listing')
        if not listing_id:
            return Response(
                {'error': 'Listing is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            listing_obj = Listing.objects.get(
                id=listing_id,
                user_profile__user=request.user
            )
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Listing does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if listing_obj.user_profile.user != request.user:
            return Response(
                {"error": "You are not authorized to create availability for this listing."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(listing=listing_obj)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

    def update(self, request, *args, **kwargs):
        """
        Update an existing availability entry.

        Restrictions:
        - Users can only update availability settings for their own listings.
        - The linked listing cannot be changed after creation.

        Raises:
            HTTP_403_FORBIDDEN: If the user does not own the listing.
            HTTP_400_BAD_REQUEST: If an attempt is made to change the linked listing.

        Args:
            request (Request): The HTTP request containing update data.

        Returns:
            Response: Updated availability data or an error message.
        """
        availability = self.get_object()

        if availability.listing.user_profile.user != request.user:
            return Response(
                {"error": "You are not authorized to update this availability."},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'listing' in request.data and str(request.data['listing']) != str(availability.listing.id):
            return Response(
                {'error': 'Listing cannot be changed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)