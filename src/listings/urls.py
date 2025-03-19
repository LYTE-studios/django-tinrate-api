from django.urls import path, include
from listings.views.listings_views import ListingView

urlpatterns = [
    path('get_listing/', ListingView.as_view(), name='listing'),
]