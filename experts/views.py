from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta

from tinrate_api.utils import success_response, error_response
from .models import Expert, Availability
from .serializers import (
    ExpertListSerializer, ExpertDetailSerializer, ExpertCreateUpdateSerializer,
    ExpertPublishSerializer, AvailabilitySerializer, AvailabilityUpdateSerializer,
    BulkAvailabilityUpdateSerializer, ProfileLinkSerializer, ProfileUrlUpdateSerializer
)
from reviews.models import Review
from reviews.serializers import ReviewSerializer
from meetings.models import Meeting
from meetings.serializers import UpcomingMeetingSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def list_experts(request):
    """
    Get list of experts with filtering and pagination.
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 100)  # Max 100 items per page
    search = request.GET.get('search', '')
    skills = request.GET.get('skills', '')
    min_rating = request.GET.get('minRating')
    max_price = request.GET.get('maxPrice')
    
    # Start with listed experts
    queryset = Expert.objects.filter(is_listed=True)
    
    # Apply search filter
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(company__icontains=search) |
            Q(bio__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    # Apply skills filter
    if skills:
        skill_list = [skill.strip() for skill in skills.split(',')]
        for skill in skill_list:
            queryset = queryset.filter(skills__contains=skill)
    
    # Apply rating filter
    if min_rating:
        try:
            min_rating = float(min_rating)
            # This would require a more complex query with review aggregation
            # For now, we'll filter based on the property method
            expert_ids = [expert.id for expert in queryset if expert.rating >= min_rating]
            queryset = queryset.filter(id__in=expert_ids)
        except ValueError:
            pass
    
    # Apply price filter
    if max_price:
        try:
            max_price = float(max_price)
            queryset = queryset.filter(hourly_rate__lte=max_price)
        except ValueError:
            pass
    
    # Order by featured, top-rated, then rating
    queryset = queryset.order_by('-is_featured', '-is_top_rated', '-created_at')
    
    # Paginate results
    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)
    
    # Serialize data
    serializer = ExpertListSerializer(page_obj.object_list, many=True)
    
    response_data = {
        'experts': serializer.data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': paginator.count,
            'totalPages': paginator.num_pages
        }
    }
    
    return success_response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_experts(request):
    """
    Get featured experts for homepage (optimized for minimal requests).
    """
    experts = Expert.objects.filter(
        is_listed=True,
        is_featured=True
    ).order_by('-created_at')[:6]  # Limit to 6 featured experts
    
    serializer = ExpertListSerializer(experts, many=True)
    
    return success_response({
        'experts': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_expert_by_profile_url(request, profile_url):
    """
    Get expert's public profile by profile URL.
    """
    expert = get_object_or_404(Expert, profile_url=profile_url, is_listed=True)
    
    # Get expert details
    expert_serializer = ExpertDetailSerializer(expert)
    
    # Get reviews
    reviews = Review.objects.filter(expert=expert).order_by('-created_at')[:10]
    review_serializer = ReviewSerializer(reviews, many=True)
    
    # Get upcoming meetings (only show count for privacy)
    upcoming_meetings_count = Meeting.objects.filter(
        expert=expert,
        status='scheduled',
        scheduled_at__gte=timezone.now()
    ).count()
    
    # Create mock upcoming meetings data (for demo purposes)
    upcoming_meetings = []
    if upcoming_meetings_count > 0:
        # In a real app, you might show some anonymized upcoming slots
        upcoming_meetings = [
            {
                'id': 'meeting_demo',
                'date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '09:00',
                'clientName': 'Upcoming Client'
            }
        ]
    
    response_data = {
        'expert': expert_serializer.data,
        'reviews': review_serializer.data,
        'upcomingMeetings': upcoming_meetings
    }
    
    return success_response(response_data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expert_listing(request):
    """
    Get or create/update expert listing.
    """
    user = request.user
    
    if request.method == 'GET':
        if not hasattr(user, 'expert_profile'):
            return error_response(
                "Expert profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        expert = user.expert_profile
        serializer = ExpertDetailSerializer(expert)
        return success_response({
            'expert': serializer.data
        })
    
    elif request.method == 'POST':
        # Check if user already has an expert profile
        try:
            expert = user.expert_profile
            serializer = ExpertCreateUpdateSerializer(expert, data=request.data, partial=True)
        except Expert.DoesNotExist:
            serializer = ExpertCreateUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            if hasattr(user, 'expert_profile'):
                expert = serializer.save()
            else:
                expert = serializer.save(user=user)
                user.is_expert = True
                user.save()
            
            response_serializer = ExpertDetailSerializer(expert)
            status_code = status.HTTP_200_OK if hasattr(user, 'expert_profile') else status.HTTP_201_CREATED
            
            return success_response({
                'expert': response_serializer.data
            }, status_code=status_code)
        
        return error_response(
            "Expert listing creation failed",
            details=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def publish_expert_listing(request):
    """
    Publish expert listing to marketplace.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    
    # Check if profile is complete enough to publish
    if not all([expert.title, expert.company, expert.bio, expert.hourly_rate, expert.skills]):
        return error_response(
            "Profile incomplete. Please fill in all required fields.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    expert.publish_listing()
    
    response_data = {
        'expert': {
            'id': str(expert.id),
            'isListed': expert.is_listed,
            'profileUrl': expert.profile_url,
            'listingUrl': f'https://tinrate.com/{expert.profile_url}'
        }
    }
    
    return success_response(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def unpublish_expert_listing(request):
    """
    Remove expert listing from marketplace.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    expert.unpublish_listing()
    
    return success_response({
        'message': 'Expert listing unpublished successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_expert_availability(request):
    """
    Get current user's availability schedule.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    month = request.GET.get('month')  # YYYY-MM format
    timezone_param = request.GET.get('timezone', 'UTC')
    
    # Get availability data
    availability_data = {
        'timezone': timezone_param,
        'schedule': [],
        'weeklyDefaults': {}
    }
    
    # Get weekly defaults
    weekly_defaults = Availability.objects.filter(
        expert=expert,
        date__isnull=True
    ).order_by('weekday', 'start_time')
    
    for weekday in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        slots = weekly_defaults.filter(weekday=weekday)
        if slots.exists():
            availability_data['weeklyDefaults'][weekday] = [
                {
                    'startTime': slot.start_time.strftime('%H:%M'),
                    'endTime': slot.end_time.strftime('%H:%M'),
                    'isEnabled': slot.is_enabled
                }
                for slot in slots
            ]
    
    # Get specific date availability if month is provided
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1).date()
            if month_num == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month_num + 1, 1).date()
            
            specific_dates = Availability.objects.filter(
                expert=expert,
                date__gte=start_date,
                date__lt=end_date
            ).order_by('date', 'start_time')
            
            # Group by date
            dates_dict = {}
            for slot in specific_dates:
                date_str = slot.date.strftime('%Y-%m-%d')
                if date_str not in dates_dict:
                    dates_dict[date_str] = []
                dates_dict[date_str].append({
                    'startTime': slot.start_time.strftime('%H:%M'),
                    'endTime': slot.end_time.strftime('%H:%M'),
                    'isAvailable': slot.is_available
                })
            
            availability_data['schedule'] = [
                {
                    'date': date,
                    'timeSlots': slots
                }
                for date, slots in dates_dict.items()
            ]
        
        except ValueError:
            return error_response(
                "Invalid month format. Use YYYY-MM.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    return success_response({
        'availability': availability_data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_expert_availability(request):
    """
    Update availability schedule.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    serializer = AvailabilityUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        timezone_param = data.get('timezone', 'UTC')
        
        # Update weekly defaults
        weekly_defaults = data.get('weeklyDefaults', {})
        if weekly_defaults:
            # Clear existing weekly defaults
            Availability.objects.filter(expert=expert, date__isnull=True).delete()
            
            # Create new weekly defaults
            for weekday, slots in weekly_defaults.items():
                for slot_data in slots:
                    Availability.objects.create(
                        expert=expert,
                        weekday=weekday,
                        start_time=slot_data['startTime'],
                        end_time=slot_data['endTime'],
                        is_enabled=slot_data.get('isEnabled', True),
                        timezone=timezone_param
                    )
        
        # Update specific dates
        specific_dates = data.get('specificDates', [])
        for date_data in specific_dates:
            date = date_data['date']
            # Clear existing slots for this date
            Availability.objects.filter(expert=expert, date=date).delete()
            
            # Create new slots for this date
            for slot_data in date_data['timeSlots']:
                Availability.objects.create(
                    expert=expert,
                    date=date,
                    start_time=slot_data['startTime'],
                    end_time=slot_data['endTime'],
                    is_available=slot_data.get('isAvailable', True),
                    timezone=timezone_param
                )
        
        return success_response({
            'message': 'Availability updated successfully'
        })
    
    return error_response(
        "Availability update failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_availability(request):
    """
    Update availability for multiple dates at once.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    serializer = BulkAvailabilityUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        dates = data['dates']
        time_slots = data['timeSlots']
        timezone_param = data['timezone']
        
        # Update availability for all specified dates
        for date in dates:
            # Clear existing slots for this date
            Availability.objects.filter(expert=expert, date=date).delete()
            
            # Create new slots for this date
            for slot_data in time_slots:
                Availability.objects.create(
                    expert=expert,
                    date=date,
                    start_time=slot_data['startTime'],
                    end_time=slot_data['endTime'],
                    is_available=True,
                    timezone=timezone_param
                )
        
        return success_response({
            'message': f'Availability updated for {len(dates)} dates'
        })
    
    return error_response(
        "Bulk availability update failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_link(request):
    """
    Get shareable profile link information.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    
    response_data = {
        'profileUrl': expert.profile_url,
        'fullUrl': f'https://tinrate.com/{expert.profile_url}',
        'isPublic': expert.is_listed
    }
    
    return success_response(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_url(request):
    """
    Update custom profile URL.
    """
    user = request.user
    
    if not hasattr(user, 'expert_profile'):
        return error_response(
            "Expert profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    expert = user.expert_profile
    serializer = ProfileUrlUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        expert.profile_url = serializer.validated_data['profileUrl']
        expert.save()
        
        response_data = {
            'profileUrl': expert.profile_url,
            'fullUrl': f'https://tinrate.com/{expert.profile_url}',
            'isPublic': expert.is_listed
        }
        
        return success_response(response_data)
    
    return error_response(
        "Profile URL update failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )
