from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    # Meeting endpoints
    path('', views.get_meetings, name='get_meetings'),
    path('stats/', views.get_meeting_stats, name='get_meeting_stats'),
    path('<uuid:meeting_id>/', views.get_meeting_detail, name='get_meeting_detail'),
    path('<uuid:meeting_id>/cancel/', views.cancel_meeting, name='cancel_meeting'),
    path('<uuid:meeting_id>/complete/', views.complete_meeting, name='complete_meeting'),
    path('<uuid:meeting_id>/reschedule/', views.reschedule_meeting, name='reschedule_meeting'),
    
    # Meeting invitation endpoints
    path('invitations/', views.get_meeting_invitations, name='get_meeting_invitations'),
    path('invitations/create/', views.create_meeting_invitation, name='create_meeting_invitation'),
    path('invitations/<uuid:invitation_id>/accept/', views.accept_meeting_invitation, name='accept_meeting_invitation'),
    path('invitations/<uuid:invitation_id>/decline/', views.decline_meeting_invitation, name='decline_meeting_invitation'),
]