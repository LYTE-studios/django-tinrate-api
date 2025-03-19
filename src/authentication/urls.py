from django.urls import path, include
from authentication.views.auth_views import RegisterView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register_view'),
    path('login/', LoginView.as_view(), name='login_view'),
    path('api-token-auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('api-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
]
