"""
URL configuration for tinrate_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings

from tinrate_api.utils import success_response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_config(request):
    """Get client configuration."""
    config_data = {
        'features': {
            'linkedinAuth': bool(settings.LINKEDIN_CLIENT_ID),
            'videoMeetings': True
        },
        'limits': {
            'maxBioLength': settings.MAX_BIO_LENGTH,
            'maxProfileUrlLength': settings.MAX_PROFILE_URL_LENGTH
        }
    }
    
    return success_response(config_data)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1 endpoints
    path('v1/auth/', include('authentication.urls')),
    path('v1/users/', include('users.urls')),
    path('v1/experts/', include('experts.urls')),
    path('v1/meetings/', include('meetings.urls')),
    path('v1/reviews/', include('reviews.urls')),
    path('v1/notifications/', include('notifications.urls')),
    
    # System endpoints
    path('v1/health/', health_check, name='health_check'),
    path('v1/config/', get_config, name='get_config'),
    
    # Search endpoint (could be moved to separate app)
    path('v1/search/', include('experts.search_urls')),
    
    # Dashboard endpoint (could be moved to separate app)
    path('v1/dashboard/', include('users.dashboard_urls')),
]
