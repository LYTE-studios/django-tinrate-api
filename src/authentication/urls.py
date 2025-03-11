from django.urls import path, include

from authentication.views.auth_views import RegisterView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register_view'),
    
]