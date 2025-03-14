from django.urls import path, include

from authentication.views.auth_views import RegisterView, LoginView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register_view'),
    path('login/', LoginView.as_view(), name='login_view'),
]