from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from rest_framework import status
from listings.serializers.listings_serializers import ListingSerializer
from listings.models.listings_models import Listing
from users.models.profile_models import UserProfile
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

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