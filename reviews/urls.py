from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review endpoints
    path('experts/<uuid:expert_id>/', views.get_expert_reviews, name='get_expert_reviews'),
    path('experts/<uuid:expert_id>/stats/', views.get_review_stats, name='get_review_stats'),
    path('meetings/<uuid:meeting_id>/', views.create_review, name='create_review'),
    
    # User review management
    path('my-reviews/', views.get_user_reviews, name='get_user_reviews'),
    path('received/', views.get_received_reviews, name='get_received_reviews'),
    path('pending/', views.get_pending_reviews, name='get_pending_reviews'),
    
    # Review actions
    path('<uuid:review_id>/', views.update_review, name='update_review'),
    path('<uuid:review_id>/delete/', views.delete_review, name='delete_review'),
    path('<uuid:review_id>/flag/', views.flag_review, name='flag_review'),
]