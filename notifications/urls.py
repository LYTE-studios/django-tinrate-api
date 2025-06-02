from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification endpoints
    path('', views.get_notifications, name='get_notifications'),
    path('stats/', views.get_notification_stats, name='get_notification_stats'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
    path('create/', views.create_notification, name='create_notification'),
    
    # Notification actions
    path('<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<uuid:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    
    # Bulk actions
    path('bulk-mark-read/', views.bulk_mark_read, name='bulk_mark_read'),
    path('bulk-delete/', views.bulk_delete_notifications, name='bulk_delete_notifications'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    
    # Notification preferences
    path('preferences/', views.get_notification_preferences, name='get_notification_preferences'),
    path('preferences/', views.update_notification_preferences, name='update_notification_preferences'),
]