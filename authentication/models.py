from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets
import string


class RefreshToken(models.Model):
    """
    Model to store refresh tokens for JWT authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="The refresh token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When the refresh token expires"
    )
    is_revoked = models.BooleanField(
        default=False,
        help_text="Whether the token has been revoked"
    )

    class Meta:
        db_table = 'refresh_tokens'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Refresh token for {self.user.email}"

    def is_expired(self):
        """Check if the refresh token has expired."""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if the refresh token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired()

    def revoke(self):
        """Revoke the refresh token."""
        self.is_revoked = True
        self.save(update_fields=['is_revoked'])

    @classmethod
    def create_for_user(cls, user):
        """Create a new refresh token for a user."""
        # Generate a secure random token
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
        
        # Set expiration to 30 days from now
        expires_at = timezone.now() + timedelta(days=30)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class LinkedInProfile(models.Model):
    """
    Model to store LinkedIn profile information for OAuth authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='linkedin_profile'
    )
    linkedin_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="LinkedIn user ID"
    )
    profile_url = models.URLField(
        blank=True,
        null=True,
        help_text="LinkedIn profile URL"
    )
    profile_data = models.JSONField(
        default=dict,
        help_text="Additional LinkedIn profile data"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'linkedin_profiles'
        verbose_name = 'LinkedIn Profile'
        verbose_name_plural = 'LinkedIn Profiles'

    def __str__(self):
        return f"LinkedIn profile for {self.user.email}"


class LoginAttempt(models.Model):
    """
    Model to track login attempts for security purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        help_text="Email address used in login attempt"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the login attempt"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    success = models.BooleanField(
        help_text="Whether the login attempt was successful"
    )
    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for login failure"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-created_at']

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.email}"

    @classmethod
    def log_attempt(cls, email, ip_address, user_agent, success, failure_reason=None):
        """Log a login attempt."""
        return cls.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent or '',
            success=success,
            failure_reason=failure_reason or ''
        )

    @classmethod
    def get_recent_failures(cls, email, hours=1):
        """Get recent failed login attempts for an email."""
        since = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(
            email=email,
            success=False,
            created_at__gte=since
        ).count()


class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        help_text="Password reset token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When the reset token expires"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Whether the token has been used"
    )

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    def is_expired(self):
        """Check if the reset token has expired."""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if the reset token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()

    def use(self):
        """Mark the token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])

    @classmethod
    def create_for_user(cls, user):
        """Create a new password reset token for a user."""
        # Generate a secure random token
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Set expiration to 1 hour from now
        expires_at = timezone.now() + timedelta(hours=1)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
