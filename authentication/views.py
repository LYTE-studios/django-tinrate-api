from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets
import string

from tinrate_api.utils import success_response, error_response
from tinrate_api.email_service import EmailService
from users.models import EmailVerification
from .models import RefreshToken as CustomRefreshToken, LoginAttempt
from .serializers import (
    LoginSerializer, RegisterSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, LinkedInAuthSerializer, LogoutSerializer
)
from users.serializers import UserSerializer

User = get_user_model()


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_verification_code():
    """Generate a 6-digit verification code."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def send_verification_email(user, verification_code):
    """Send verification email to user."""
    try:
        success = EmailService.send_verification_email(user, verification_code)
        if success:
            print(f"✅ Verification email sent successfully to {user.email}")
        else:
            print(f"❌ Failed to send verification email to {user.email}")
        return success
    except Exception as e:
        print(f"❌ Error sending verification email to {user.email}: {str(e)}")
        return False


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account.
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate and send verification code
        verification_code = generate_verification_code()
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerification.objects.create(
            user=user,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        send_verification_email(user, verification_code)
        
        # Log successful registration
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        LoginAttempt.log_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        response_data = {
            'user': UserSerializer(user).data,
            'requiresEmailVerification': True
        }
        
        return success_response(response_data, status_code=status.HTTP_201_CREATED)
    
    return error_response(
        "Registration failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return access token.
    """
    serializer = LoginSerializer(data=request.data)
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Check if email is verified
        if not user.is_email_verified:
            LoginAttempt.log_attempt(
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='Email not verified'
            )
            return error_response(
                "Email not verified",
                details={"requiresEmailVerification": True},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Store custom refresh token
        CustomRefreshToken.create_for_user(user)
        
        # Log successful login
        LoginAttempt.log_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        response_data = {
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': UserSerializer(user).data
        }
        
        return success_response(response_data)
    
    # Log failed login attempt
    email = request.data.get('email', '')
    if email:
        LoginAttempt.log_attempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason='Invalid credentials'
        )
    
    return error_response(
        "Invalid credentials",
        details=serializer.errors,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user's email address with verification code.
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        verification = serializer.validated_data['verification']
        
        # Mark verification as used
        verification.is_used = True
        verification.save()
        
        # Mark user email as verified
        user.is_email_verified = True
        user.save()
        
        # Generate JWT tokens for automatic authentication
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Store custom refresh token
        CustomRefreshToken.create_for_user(user)
        
        # Log successful verification/login
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        LoginAttempt.log_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Send welcome email
        try:
            EmailService.send_welcome_email(user)
        except Exception as e:
            # Don't fail the verification if welcome email fails
            print(f"Warning: Failed to send welcome email to {user.email}: {str(e)}")
        
        response_data = {
            'message': 'Email verified successfully',
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': UserSerializer(user).data
        }
        
        return success_response(response_data)
    
    return error_response(
        "Email verification failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """
    Resend email verification code.
    """
    serializer = ResendVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate new verification code
        verification_code = generate_verification_code()
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerification.objects.create(
            user=user,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        send_verification_email(user, verification_code)
        
        return success_response({
            'message': 'Verification code sent successfully'
        })
    
    return error_response(
        "Failed to resend verification",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user and invalidate tokens.
    """
    serializer = LogoutSerializer(data=request.data)
    if serializer.is_valid():
        # Revoke all refresh tokens for the user
        CustomRefreshToken.objects.filter(user=request.user).update(is_revoked=True)
        
        return success_response({
            'message': 'Logged out successfully'
        })
    
    return error_response(
        "Logout failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def linkedin_auth(request):
    """
    Authenticate with LinkedIn OAuth.
    """
    serializer = LinkedInAuthSerializer(data=request.data)
    if serializer.is_valid():
        linkedin_data = serializer.validated_data['linkedin_data']
        
        # Check if user exists with this email
        try:
            user = User.objects.get(email=linkedin_data['email'])
        except User.DoesNotExist:
            # Create new user from LinkedIn data
            user = User.objects.create_user(
                email=linkedin_data['email'],
                first_name=linkedin_data['firstName'],
                last_name=linkedin_data['lastName'],
                is_email_verified=True,  # LinkedIn emails are pre-verified
                profile_complete=True
            )
        
        # Update or create LinkedIn profile
        from .models import LinkedInProfile
        linkedin_profile, created = LinkedInProfile.objects.get_or_create(
            user=user,
            defaults={
                'linkedin_id': linkedin_data['id'],
                'profile_data': linkedin_data
            }
        )
        
        if not created:
            linkedin_profile.profile_data = linkedin_data
            linkedin_profile.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Store custom refresh token
        CustomRefreshToken.create_for_user(user)
        
        # Log successful login
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        LoginAttempt.log_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        response_data = {
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': UserSerializer(user).data
        }
        
        return success_response(response_data)
    
    return error_response(
        "LinkedIn authentication failed",
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh JWT access token using refresh token.
    """
    refresh_token = request.data.get('refreshToken')
    
    if not refresh_token:
        return error_response(
            "Refresh token required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate custom refresh token
        custom_token = CustomRefreshToken.objects.get(token=refresh_token)
        if not custom_token.is_valid():
            return error_response(
                "Invalid or expired refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate new access token
        refresh = RefreshToken.for_user(custom_token.user)
        access_token = str(refresh.access_token)
        new_refresh_token = str(refresh)
        
        # Revoke old refresh token and create new one
        custom_token.revoke()
        CustomRefreshToken.create_for_user(custom_token.user)
        
        response_data = {
            'accessToken': access_token,
            'refreshToken': new_refresh_token
        }
        
        return success_response(response_data)
    
    except CustomRefreshToken.DoesNotExist:
        return error_response(
            "Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
