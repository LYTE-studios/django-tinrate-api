from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User profile endpoints
    path('me/', views.get_current_user, name='get_current_user'),
    path('me/', views.update_current_user, name='update_current_user'),
    path('me/complete-profile/', views.complete_profile, name='complete_profile'),
    path('me/stats/', views.get_user_stats, name='get_user_stats'),
    path('me/activity/', views.get_user_activity, name='get_user_activity'),
    path('me/upload-image/', views.upload_profile_image, name='upload_profile_image'),
    path('me/change-email/', views.change_email, name='change_email'),
    path('me/delete/', views.delete_account, name='delete_account'),
]