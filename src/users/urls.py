from django.urls import path, include
from users.views.user_views import UserView

urlpatterns = [
    path('user_view/', UserView.as_view(), name='user_view'),
]