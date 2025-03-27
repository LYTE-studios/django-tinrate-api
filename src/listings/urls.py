from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.views.listings_views import (
    ListingViewSet,
    DayViewSet,
    AvailabilityViewSet
)
router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listings')
router.register(r'availabilities', AvailabilityViewSet, basename='availabilities')
router.register(r'days', DayViewSet, basename='days')

urlpatterns = [
    
] + router.urls