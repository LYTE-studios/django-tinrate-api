from django.urls import path, include
from users.views.user_views import UserView
from users.views.profile_views import UserProfileView, ExperienceView, RoleView, CompanyView
from users.views.settings_views import SettingsView

urlpatterns = [
    path('get_users/', UserView.as_view(), name='users'),
    path('get_user_profile/', UserProfileView.as_view(), name='user_profile'),
    path('get_user_experience/', ExperienceView.as_view(), name='user_experience'),
    path('get_user_role/', RoleView.as_view(), name='user_role'),
    path('get_user_company/', CompanyView.as_view(), name='user_company'),
    path('get_settings/', SettingsView.as_view(), name='settings'),
    
]