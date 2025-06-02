from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def cors_test(request):
    """
    Simple CORS test endpoint to verify CORS configuration is working.
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = JsonResponse({'message': 'CORS preflight successful'})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Handle actual request
    data = {
        'message': 'CORS test successful',
        'method': request.method,
        'origin': request.META.get('HTTP_ORIGIN', 'No origin header'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'No user agent'),
        'headers': {
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'authorization': request.META.get('HTTP_AUTHORIZATION', 'No auth header'),
        }
    }
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8')) if request.body else {}
            data['body'] = body
        except json.JSONDecodeError:
            data['body'] = 'Invalid JSON'
    
    return JsonResponse(data)

urlpatterns = [
    path('cors-test/', cors_test, name='cors_test'),
]