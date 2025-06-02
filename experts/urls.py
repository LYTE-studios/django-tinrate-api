from django.urls import path
from . import views

app_name = 'experts'

urlpatterns = [
    # Expert listing endpoints
    path('', views.list_experts, name='list_experts'),
    path('featured/', views.featured_experts, name='featured_experts'),
    path('<str:profile_url>/', views.get_expert_by_profile_url, name='get_expert_by_profile_url'),
    
    # Expert profile management
    path('me/listing/', views.create_expert_listing, name='create_expert_listing'),
    path('me/listing/publish/', views.publish_expert_listing, name='publish_expert_listing'),
    path('me/listing/unpublish/', views.unpublish_expert_listing, name='unpublish_expert_listing'),
    
    # Availability management
    path('me/availability/', views.get_expert_availability, name='get_expert_availability'),
    path('me/availability/', views.update_expert_availability, name='update_expert_availability'),
    path('me/availability/bulk-update/', views.bulk_update_availability, name='bulk_update_availability'),
    
    # Profile sharing
    path('me/profile-link/', views.get_profile_link, name='get_profile_link'),
    path('me/profile-url/', views.update_profile_url, name='update_profile_url'),
]