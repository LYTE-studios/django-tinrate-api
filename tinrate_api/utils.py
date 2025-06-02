from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses
    following the TinRate API specification format.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'An error occurred',
                'details': response.data
            }
        }
        
        # Handle specific error types
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['error']['message'] = 'Bad request'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['error']['message'] = 'Unauthorized'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['error']['message'] = 'Forbidden'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['error']['message'] = 'Not found'
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data['error']['message'] = 'Rate limit exceeded'
        elif response.status_code >= 500:
            custom_response_data['error']['message'] = 'Internal server error'
            logger.error(f"Server error: {exc}", exc_info=True)
        
        response.data = custom_response_data
    
    return response


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Helper function to create consistent success responses
    following the TinRate API specification format.
    """
    response_data = {
        'success': True,
        'data': data or {}
    }
    
    if message:
        response_data['data']['message'] = message
    
    return Response(response_data, status=status_code)


def error_response(message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Helper function to create consistent error responses
    following the TinRate API specification format.
    """
    response_data = {
        'success': False,
        'error': {
            'message': message
        }
    }
    
    if details:
        response_data['error']['details'] = details
    
    return Response(response_data, status=status_code)


class StandardResultsSetPagination:
    """
    Custom pagination class that returns paginated results
    in the format specified by the TinRate API.
    """
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': {
                'results': data,
                'pagination': {
                    'page': self.page.number,
                    'limit': self.page.paginator.per_page,
                    'total': self.page.paginator.count,
                    'totalPages': self.page.paginator.num_pages,
                }
            }
        })