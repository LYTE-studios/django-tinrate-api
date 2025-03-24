from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views.user_views import UserView
from users.views.profile_views import (
    UserProfileViewSet,
    ExperienceViewSet,
    CareerViewSet,
    EducationViewSet,
    ReviewViewSet,
)
from users.views.settings_views import (
    ProfileSettingsViewSet,
    PasswordSettingsViewSet,
    NotificationPreferencesViewSet,
    PaymentSettingsViewSet,
    SupportTicketViewSet,
    SettingsViewSet
)

router = DefaultRouter()
router.register(r'user_profile', UserProfileViewSet, basename='user_profile')
router.register(r'user_experiences', ExperienceViewSet, basename='user_experiences')
router.register(r'user_careers', CareerViewSet, basename='user_careers')
router.register(r'user_educations', EducationViewSet, basename='user_educations')
router.register(r'user_reviews', ReviewViewSet, basename='user_reviews')

router.register(r'profile_settings', ProfileSettingsViewSet, basename='profile_settings')
router.register(r'password_settings', PasswordSettingsViewSet, basename='password_settings')
router.register(r'notification_preferences', NotificationPreferencesViewSet, basename='notification_preferences')
router.register(r'payment_settings', PaymentSettingsViewSet, basename='payment_settings')
router.register(r'support_tickets', SupportTicketViewSet, basename='support_tickets')
router.register(r'general_settings', SettingsViewSet, basename='general_settings')

urlpatterns = [
    path('user_view/', UserView.as_view(), name='user_view'),
] + router.urls