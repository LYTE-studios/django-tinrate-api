from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.contrib.auth import get_user_model
from users.models.profile_models import UserProfile, Experience, Career, Education, Review
from users.serializers.user_profile_serializers import (
    UserProfileSerializer,
    UserProfileCreateUpdateSerializer,
    ExperienceSerializer,
    CareerSerializer,
    EducationSerializer,
    ReviewSerializer
)

User = get_user_model()

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user profiles.

    This viewset provides actions to:
    - List all user profiles or filter by `country` and `job_title`.
    - Retrieve a single user profile.
    - Create a new user profile (with user permissions).
    - Update or partially update an existing user profile (with user permissions).
    - Delete a user profile (with user permissions).
    - Update statistics related to the user profile, such as total meetings, completed meetings, and total minutes.
    - List experiences associated with a user profile.

    Custom actions:
    - `experiences`: Lists all experiences related to the user profile.
    - `update_statistics`: Updates statistics like total meetings, meetings completed, and total minutes.
    """
    def get_queryset(self):
        """
        Returns a filtered queryset of UserProfiles based on query parameters.

        - Filters by 'country' if the 'country' query parameter is provided.
        - Filters by 'job_title' if the 'job_title' query parameter is provided.

        Query parameters:
            country (str): The country to filter profiles by.
            job_title (str): The job title to filter profiles by.

        Returns:
            QuerySet: A filtered queryset of UserProfile objects.
        """
        queryset = UserProfile.objects.all()

        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__icontains=country)

        job_title = self.request.query_params.get('job_title', None)
        if job_title:
            queryset = queryset.filter(job_title__icontains=job_title)
        return queryset
    
    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the action being performed.

        - For 'create', 'update', or 'partial_update' actions, it returns the UserProfileCreateUpdateSerializer.
        - For other actions like 'list' and 'retrieve', it returns the UserProfileSerializer.

        Returns:
            class: The serializer class to be used for the current action.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return UserProfileCreateUpdateSerializer
        return UserProfileSerializer
    
    def perform_create(self, serializer):
        """
        Custom method to handle the creation of a UserProfile.

        - Checks if the user already has a profile. If a profile exists, returns a 400 Bad Request response.
        - If the user doesn't have a profile, saves the profile with the current authenticated user.

        Args:
            serializer (serializers.ModelSerializer): The serializer instance containing validated data.
        """
        if hasattr(self.request.user, 'user_profile'):
            return Response(
                {"detail": "User profile already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Handles the update of a UserProfile. Ensures the user can only update their own profile.

        Arguments:
            request (Request): The request object containing the data to update the profile.
            *args: Additional arguments to pass to the parent class method.
            **kwargs: Additional keyword arguments, including the 'partial' flag.

        Returns:
            Response: The response with the updated profile data or an error if unauthorized.
        
        Raises:
            ValidationError: If the provided data is invalid.
        """

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permissions to update this profile."},
                status=status.HTTP_403_FORBIDDEN   
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles the deletion of a UserProfile. Ensures the user can only delete their own profile.

        Arguments:
            request (Request): The request object for deleting the profile.
            *args: Additional arguments to pass to the parent class method.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: The response with a 204 status code if successful, or an error if unauthorized.
        """
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permissions to delete this profile."},
                status=status.HTTP_403_FORBIDDEN  
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def experiences(self, request, pk=None):
        """
        Retrieves all experiences associated with a specific UserProfile.

        Arguments:
            request (Request): The request object.
            pk (int): The primary key of the UserProfile whose experiences are being fetched.

        Returns:
            Response: A list of experiences related to the specified UserProfile.
        """
        profile = self.get_object()
        experiences = Experience.objects.filter(user_profile=profile)
        serializer = ExperienceSerializer(experiences, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def careers(self, request, pk=None):
        """
        Retrieves all careers associated with a specific UserProfile.

        Arguments:
            request (Request): The request object.
            pk (int): The primary key of the UserProfile whose careers are being fetched.

        Returns:
            Response: A list of careers related to the specified UserProfile.
        """
        profile = self.get_object()
        careers = Career.objects.filter(user_profile=profile)
        serializer = CareerSerializer(careers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def educations(self, request, pk=None):
        """
        Retrieves all educations associated with a specific UserProfile.

        Arguments:
            request (Request): The request object.
            pk (int): The primary key of the UserProfile whose educations are being fetched.

        Returns:
            Response: A list of educations related to the specified UserProfile.
        """
        profile = self.get_object()
        educations = Education.objects.filter(user_profile=profile)
        serializer = EducationSerializer(educations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Retrieves all reviews associated with a specific UserProfile.

        Arguments:
            request (Request): The request object.
            pk (int): The primary key of the UserProfile whose reviews are being fetched.

        Returns:
            Response: A list of reviews related to the specified UserProfile.
        """
        profile = self.get_object()
        reviews = Review.objects.filter(user_profile=profile)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_statistics(self, request, pk=None):
        """
        Updates statistics for a UserProfile, including total meetings, meetings completed,
        and total minutes. Only the user who owns the profile can update their statistics.

        Arguments:
            request (Request): The request object containing the data to update the profile's statistics.
            pk (int): The primary key of the UserProfile whose statistics are being updated.

        Returns:
            Response: The updated UserProfile data if successful, or an error message if unauthorized.

        Raises:
            ValidationError: If the provided data is invalid.
        """

        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to update these statistics."},
                status=status.HTTP_403_FORBIDDEN  
            )
        total_meetings = request.data.get('total_meetings')
        meetings_completed = request.data.get('meetings_completed')
        total_minutes = request.data.get('total_minutes')

        if total_meetings is not None:
            profile.total_meetings = total_meetings

        if meetings_completed is not None:
            profile.meetings_completed = meetings_completed

        if total_minutes is not None:
            profile.total_minutes = total_minutes

        profile.save()
        return Response(UserProfileSerializer(profile).data)
    

class ExperienceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the experiences of a user's profile.

    Provides CRUD operations for experiences, allowing users to:
    - Create an experience (requires a user profile).
    - Update an experience (only allowed for the owner).
    - Delete an experience (only allowed for the owner).
    - List experiences of the authenticated user.

    The Experience model is associated with a user profile, and only the owner of the profile can manage their experiences.
    """
    
    def get_queryset(self):
        """
        Returns the list of experiences for the authenticated user.

        Filters experiences to only include those associated with the current user.

        Returns:
            queryset (QuerySet): A queryset containing the user's experiences.
        """
        return Experience.objects.filter(user_profile__user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Saves a new experience, associating it with the user's profile.

        Checks if the user has a profile. If not, returns a bad request error.

        Args:
            serializer (ExperienceSerializer): The serializer instance used to validate and save the new experience.
        """
        try:
            profile = self.request.user.user_profile
            serializer.save(user_profile=profile)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "You must create a profile before adding experiences."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Updates an existing experience.

        Ensures the user can only update experiences they own. If the experience is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object containing the data to update.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: The updated experience data, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to update this experience."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """
        Deletes an experience.

        Ensures the user can only delete experiences they own. If the experience is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: An empty response with status 204 (No Content) if successful, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to delete this experience."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)
    

class CareerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the careers of a user's profile.

    Provides CRUD operations for careers, allowing users to:
    - Create an career (requires a user profile).
    - Update an career (only allowed for the owner).
    - Delete an career (only allowed for the owner).
    - List career of the authenticated user.

    The Career model is associated with a user profile, and only the owner of the profile can manage their careers.
    """
    
    def get_queryset(self):
        """
        Returns the list of careers for the authenticated user.

        Filters careers to only include those associated with the current user.

        Returns:
            queryset (QuerySet): A queryset containing the user's careers.
        """
        return Career.objects.filter(user_profile__user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Saves a new career, associating it with the user's profile.

        Checks if the user has a profile. If not, returns a bad request error.

        Args:
            serializer (CareerSerializer): The serializer instance used to validate and save the new career.
        """
        try:
            profile = self.request.user.user_profile
            serializer.save(user_profile=profile)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "You must create a profile before adding careers."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Updates an existing career.

        Ensures the user can only update careers they own. If the career is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object containing the data to update.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: The updated career data, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to update this career."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """
        Deletes a career.

        Ensures the user can only delete careers they own. If the career is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: An empty response with status 204 (No Content) if successful, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to delete this career."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)
    

class EducationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the educations of a user's profile.

    Provides CRUD operations for educations, allowing users to:
    - Create an education (requires a user profile).
    - Update an education (only allowed for the owner).
    - Delete an education (only allowed for the owner).
    - List education of the authenticated user.

    The Education model is associated with a user profile, and only the owner of the profile can manage their educations.
    """
    
    def get_queryset(self):
        """
        Returns the list of educations for the authenticated user.

        Filters educations to only include those associated with the current user.

        Returns:
            queryset (QuerySet): A queryset containing the user's educations.
        """
        return Education.objects.filter(user_profile__user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Saves a new education, associating it with the user's profile.

        Checks if the user has a profile. If not, returns a bad request error.

        Args:
            serializer (EducationSerializer): The serializer instance used to validate and save the new education.
        """
        try:
            profile = self.request.user.user_profile
            serializer.save(user_profile=profile)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "You must create a profile before adding educations."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Updates an existing education.

        Ensures the user can only update education they own. If the education is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object containing the data to update.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: The updated education data, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to update this education."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """
        Deletes a education.

        Ensures the user can only delete education they own. If the education is not owned by the requesting user, returns a forbidden error.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: An empty response with status 204 (No Content) if successful, or an error message if permissions are not met.
        """
        instance = self.get_object()
        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "You do not have permissions to delete this education."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)
    

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews between users. Allows authenticated users to:
    - Create a review for another user's profile.
    - Update an existing review they have written.
    - Delete a review they have written.
    - The review is associated with a user profile, and the profile's rating is updated after each action.

    Reviews can only be created for other users' profiles, not for the user's own profile.
    Reviews can only be updated or deleted by the reviewer who created them.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the reviews created by the authenticated user.

        Returns:
            queryset (QuerySet): A queryset containing all reviews written by the current user.
        """
        return Review.objects.filter(reviewer=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Creates a new review for a user profile.

        Validates the input data, checks that the profile exists, and ensures that:
        - The user is not reviewing their own profile.
        - The user has not already reviewed the profile.
        
        The review is associated with the authenticated user and the target user profile.
        After the review is created, the target user's rating is recalculated based on all of their reviews.

        Args:
            request (Request): The HTTP request object containing the review data.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: The created review data or an error message if validation fails.
        """
        profile_id = request.data.get('user_profile')
        if not profile_id:
            return Response(
                {"detail": "User profile ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if profile.user == request.user:
            return Response(
                {"detail": "You cannot review your own profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if Review.objects.filter(user_profile=profile, reviewer=request.user).exists():
            return Response(
                {"detail": "You have already reviewed this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_profile=profile, reviewer=request.user)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Updates an existing review.

        Ensures that the user who is updating the review is the same user who created the review.
        After updating the review, the target user's rating is recalculated based on all their reviews.

        Args:
            request (Request): The HTTP request object containing the updated review data.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: The updated review data or an error message if the user does not have permission.
        """
        instance = get_user_model()

        if instance.reviewer != request.user:
            return Response(
                {"detail": "You do not have permissions to update this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        response = super().update(request, *args, **kwargs)

        return response

    def destroy(self, request, *args, **kwargs):
        """
        Deletes an existing review.

        Ensures that the user who is deleting the review is the same user who created the review.
        After deleting the review, the target user's rating is recalculated based on all their reviews.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Additional positional arguments passed to the view's method.
            **kwargs (dict): Additional keyword arguments passed to the view's method.

        Returns:
            Response: An empty response with status 204 (No Content) if successful, or an error message if the user does not have permission.
        """
        instance = get_user_model()

        if instance.reviewer != request.user:
            return Response(
                {"detail": "You do not have permissions to delete this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        response = super().destroy(request, *args, **kwargs)


        return response

    