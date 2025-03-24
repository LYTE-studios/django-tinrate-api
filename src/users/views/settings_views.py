from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from users import serializers
from users.models import (
    UserProfile,
    NotificationPreferences,
    PaymentSettings,
    SupportTicket,
    Settings
)
from users.serializers.user_settings_serializers import (
    ProfileSettingsSerializer,
    PasswordChangeSerializer,
    NotificationPreferencesSerializer,
    PaymentSettingsSerializer,
    SupportTicketSerializer,
    SettingsSerializer
)

class ProfileSettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing profile settings.

    Attributes:
        serializer_class (ProfileSettingsSerializer): Serializer used for profile settings.
        permission_classes (list): List of permissions required for this viewset.

    Methods:
        get_object():
            Retrieves the user profile for the authenticated user.
        retrieve_profile(request):
            Retrieves the current user's profile settings.
        update_profile(request):
            Updates the user's profile settings (PUT/PATCH).
    """
    serializer_class = ProfileSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieve the UserProfile instance for the authenticated user.
        
        Returns:
            UserProfile: The user's profile instance.
        """
        return get_object_or_404(UserProfile, user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def retrieve_profile(self, request):
        """
        Retrieves the profile settings for the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing the user's profile data.
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Updates the profile settings for the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing updated profile data or validation errors.
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, 
                                         data=request.data,
                                         partial=request.method=='PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PasswordSettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for changing user passwords.

    Attributes:
        serializer_class (PasswordChangeSerializer): Serializer for password change.
        permission_classes (list): List of permissions required.

    Methods:
        change_password(request):
            Allows an authenticated user to change their password.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Changes the authenticated user's password.

        Args:
            request (Request): The HTTP request object containing 'new_password'.

        Returns:
            Response: Success message if password change is successful, otherwise error messages.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({"detail":"Password updated successfully."},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class NotificationPreferencesViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing notification preferences.

    Attributes:
        serializer_class (NotificationPreferencesSerializer): Serializer for notification preferences.
        permission_classes (list): List of permissions required.

    Methods:
        get_object():
            Retrieves or creates notification preferences for the user.
        retrieve_preferences(request):
            Retrieves the user's notification preferences.
        update_preferences(request):
            Updates the user's notification preferences (PUT/PATCH).
    """
    serializer_class = NotificationPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves or creates notification preferences for the authenticated user.

        Returns:
            NotificationPreferences: The notification preferences instance.
        """
        obj, created = NotificationPreferences.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    @action(detail=False, methods=['get'])
    def retrieve_preferences(self, request):
        """
        Retrieves the notification preferences of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response with notification preferences.
        """
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """
        Updates the notification preferences of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response with updated preferences or validation errors.
        """
        preferences = self.get_object()
        serializer = self.get_serializer(preferences,
                                         data=request.data,
                                         partial=request.method=='PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PaymentSettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing payment settings.

    Attributes:
        serializer_class (PaymentSettingsSerializer): Serializer for payment settings.
        permission_classes (list): List of permissions required.

    Methods:
        get_object():
            Retrieves or creates payment settings for the user.
        retrieve_settings(request):
            Retrieves the user's payment settings.
        update_settings(request):
            Updates the user's payment settings (PUT/PATCH).
    """
    serializer_class = PaymentSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves or creates payment settings for the authenticated user.

        Returns:
            PaymentSettings: The payment settings instance.
        """
        obj, created = PaymentSettings.objects.get_or_create(
            user=self.request.user
        )
        return obj
    @action(detail=False, methods=['get'])
    def retrieve_settings(self, request):
        """
        Retrieves the payment settings of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response with payment settings.
        """
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_settings(self, request):
        """
        Updates the payment settings of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response with updated payment settings or validation errors.
        """
        settings = self.get_object()
        serializer = self.get_serializer(settings,
                                         data=request.data,
                                         partial=request.method=='PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SupportTicketViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing user support tickets.

    Attributes:
        serializer_class (SupportTicketSerializer): Serializer for handling support tickets.
        permission_classes (list): List of permissions required for accessing support tickets.

    Methods:
        get_queryset():
            Retrieves all support tickets created by the authenticated user.
        perform_create(serializer):
            Saves a new support ticket with the authenticated user as the owner.
        list(request):
            Returns a list of all support tickets belonging to the authenticated user.
        retrieve(request, pk):
            Retrieves a single support ticket by ID if it belongs to the authenticated user.
    """
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the list of support tickets for the authenticated user.

        Returns:
            QuerySet: A queryset containing the support tickets associated with the user.
        """
        return SupportTicket.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer) ->None:
        """
        Creates a new support ticket for the authenticated user.

        Args:
            serializer (SupportTicketSerializer): The serializer containing validated ticket data.

        """
        serializer.save(user=self.request.user)

    def list(self, request):
        """
        Returns a list of all support tickets for the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing all support tickets of the user.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieves a single support ticket belonging to the authenticated user.

        Args:
            request (Request): The HTTP request object.
            pk (int, optional): The primary key of the support ticket.

        Returns:
            Response: JSON response containing the requested support ticket details.
        """
        ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


class SettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing user settings.

    Attributes:
        serializer_class (SettingsSerializer): Serializer for handling user settings.
        permission_classes (list): List of permissions required for accessing settings.

    Methods:
        get_object():
            Retrieves or creates a settings instance for the authenticated user.
        retrieve_settings(request):
            Retrieves the general settings for the authenticated user.
        profile(request):
            Retrieves or updates the profile settings.
        account_security(request):
            Retrieves or updates the account security settings.
        notification_pref(request):
            Retrieves or updates the notification preferences.
        payment_settings(request):
            Retrieves or updates the payment settings.
        support_help(request):
            Retrieves or updates the support and help settings.
    """
    serializer_class = SettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves or creates a settings instance for the authenticated user.

        Returns:
            Settings: The settings instance associated with the user.
        """
        obj, created = Settings.objects.get_or_create(user=self.request.user)
        return obj
    
    @action(detail=False, methods=['get'])
    def retrieve_settings(self, request):
        """
        Retrieves the general settings of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response with general settings data.
        """
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """
        Retrieves or updates the profile settings of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing profile settings or an updated response.
        """
        settings = self.get_object()
        if request.method == 'GET':
            return Response(settings.profile)
        settings.profile = request.data
        settings.save(update_fields=['profile'])
        return Response(settings.profile)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def account_security(self, request):
        """
        Retrieves or updates the account security settings.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing account security settings or updated response.
        """
        settings = self.get_object()
        if request.method == 'GET':
            return Response(settings.account_security)
        
        settings.account_security = request.data
        settings.save(update_fields=['account_security'])
        return Response(settings.account_security)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def notification_pref(self, request):
        """
        Retrieves or updates the notification preferences.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing notification preferences or updated response.
        """
        settings = self.get_object()
        if request.method == 'GET':
            return Response(settings.notification_pref)
        
        settings.notification_pref = request.data
        settings.save(update_fields=['notification_pref'])
        return Response(settings.notification_pref)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def payment_settings(self, request):
        """
        Retrieves or updates the payment settings.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing payment settings or updated response.
        """
        settings = self.get_object()
        if request.method == 'GET':
            return Response(settings.payment_settings)
        
        settings.payment_settings = request.data
        settings.save(update_fields=['payment_settings'])
        return Response(settings.payment_settings)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def support_help(self, request):
        """
        Retrieves or updates the support and help settings.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: JSON response containing support settings or updated response.
        """
        settings = self.get_object()
        if request.method == 'GET':
            return Response(settings.support_help)
        
        settings.support_help = request.data
        settings.save(update_fields=['support_help'])
        return Response(settings.support_help)
    

