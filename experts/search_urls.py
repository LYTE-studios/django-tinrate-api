from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.core.paginator import Paginator

from tinrate_api.utils import success_response, error_response
from .models import Expert
from .serializers import ExpertListSerializer

app_name = 'search'


@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    """
    Global search across experts and content.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # experts, all
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    if not query:
        return error_response(
            "Search query required",
            status_code=400
        )
    
    results = {
        'experts': [],
        'totalResults': 0
    }
    
    # Search experts
    if search_type in ['experts', 'all']:
        expert_queryset = Expert.objects.filter(
            is_listed=True
        ).filter(
            Q(title__icontains=query) |
            Q(company__icontains=query) |
            Q(bio__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(skills__icontains=query)
        ).distinct()
        
        # Limit results
        experts = expert_queryset[:limit]
        expert_serializer = ExpertListSerializer(experts, many=True)
        
        results['experts'] = expert_serializer.data
        results['totalResults'] = expert_queryset.count()
    
    return success_response(results)


urlpatterns = [
    path('', global_search, name='global_search'),
]