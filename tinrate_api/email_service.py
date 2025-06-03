"""
Email service for TinRate API.
Handles sending various types of emails including verification, notifications, etc.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling email operations."""
    
    @staticmethod
    def _get_email_context(user, **kwargs):
        """
        Get common context variables for email templates.
        
        Args:
            user: User instance
            **kwargs: Additional context variables
        """
        context = {
            'user': user,
            'support_email': settings.TINRATE_SUPPORT_EMAIL,
            'base_url': settings.TINRATE_BASE_URL,
        }
        context.update(kwargs)
        return context
    
    @staticmethod
    def _send_templated_email(user, subject, template_name, context=None):
        """
        Send an email using Django templates.
        
        Args:
            user: User instance
            subject: Email subject
            template_name: Template name (without extension)
            context: Additional template context
        """
        try:
            # Prepare context
            email_context = EmailService._get_email_context(user, **(context or {}))
            
            # Render templates
            html_content = render_to_string(f'emails/{template_name}.html', email_context)
            text_content = render_to_string(f'emails/{template_name}.txt', email_context)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.TINRATE_FROM_EMAIL,
                to=[user.email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email '{subject}' sent successfully to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email '{subject}' to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(user, verification_code):
        """
        Send email verification code to user.
        
        Args:
            user: User instance
            verification_code: 6-digit verification code
        """
        return EmailService._send_templated_email(
            user=user,
            subject='Verify your TinRate account',
            template_name='verification',
            context={'verification_code': verification_code}
        )
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """
        Send password reset email to user.
        
        Args:
            user: User instance
            reset_token: Password reset token
        """
        reset_url = f"{settings.TINRATE_BASE_URL}/reset-password?token={reset_token}"
        
        return EmailService._send_templated_email(
            user=user,
            subject='Reset your TinRate password',
            template_name='password_reset',
            context={'reset_url': reset_url}
        )
    
    @staticmethod
    def send_welcome_email(user):
        """
        Send welcome email after successful email verification.
        
        Args:
            user: User instance
        """
        return EmailService._send_templated_email(
            user=user,
            subject='Welcome to TinRate - Your account is ready!',
            template_name='welcome'
        )