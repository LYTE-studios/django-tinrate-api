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

router = DefaultRouter()
router.register(r'user_profile', UserProfileViewSet, basename='user_profile'),
router.register(r'user_experiences', ExperienceViewSet, basename='user_experiences'),
router.register(r'user_careers', CareerViewSet, basename='user_careers')
router.register(r'user_educations', EducationViewSet, basename='user_educations')
router.register(r'user_reviews', ReviewViewSet, basename='user_reviews')

urlpatterns = [
    path('user_view/', UserView.as_view(), name='user_view'),
] + router.urls