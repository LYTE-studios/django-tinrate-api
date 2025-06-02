from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import EmailValidator
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser
    to match the TinRate API specification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="User's email address"
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name"
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        help_text="User's country code (ISO 3166-1 alpha-2)"
    )
    profile_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to user's profile image"
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    profile_complete = models.BooleanField(
        default=False,
        help_text="Whether the user has completed their profile"
    )
    is_expert = models.BooleanField(
        default=False,
        help_text="Whether the user is an expert"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the username field
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def mark_profile_complete(self):
        """Mark the user's profile as complete if required fields are filled."""
        if self.first_name and self.last_name and self.country:
            self.profile_complete = True
            self.save(update_fields=['profile_complete'])


class EmailVerification(models.Model):
    """
    Model to store email verification codes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verifications'
    )
    verification_code = models.CharField(
        max_length=6,
        help_text="6-digit verification code"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When the verification code expires"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Whether the verification code has been used"
    )

    class Meta:
        db_table = 'email_verifications'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification for {self.user.email}"

    def is_expired(self):
        """Check if the verification code has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if the verification code is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()
