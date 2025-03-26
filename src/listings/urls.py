from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.views.listings_views import (
    ListingViewSet,

)
router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listings')

urlpatterns = [
    
] + router.urls