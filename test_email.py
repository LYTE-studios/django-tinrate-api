#!/usr/bin/env python3
"""
Test script to verify email functionality.
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinrate_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from tinrate_api.email_service import EmailService

User = get_user_model()

def test_email_service():
    """Test the email service functionality."""
    print("🧪 Testing TinRate Email Service")
    print("=" * 50)
    
    # Check email configuration
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email Host: {settings.EMAIL_HOST}")
    print(f"📧 Email Port: {settings.EMAIL_PORT}")
    print(f"📧 Email User: {settings.EMAIL_HOST_USER}")
    print(f"📧 From Email: {settings.TINRATE_FROM_EMAIL}")
    print()
    
    # Create a test user (don't save to database)
    test_user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    
    print("🔍 Testing verification email...")
    try:
        success = EmailService.send_verification_email(test_user, "123456")
        if success:
            print("✅ Verification email test passed!")
        else:
            print("❌ Verification email test failed!")
    except Exception as e:
        print(f"❌ Verification email test error: {e}")
    
    print()
    print("🔍 Testing welcome email...")
    try:
        success = EmailService.send_welcome_email(test_user)
        if success:
            print("✅ Welcome email test passed!")
        else:
            print("❌ Welcome email test failed!")
    except Exception as e:
        print(f"❌ Welcome email test error: {e}")
    
    print()
    print("🔍 Testing password reset email...")
    try:
        success = EmailService.send_password_reset_email(test_user, "reset-token-123")
        if success:
            print("✅ Password reset email test passed!")
        else:
            print("❌ Password reset email test failed!")
    except Exception as e:
        print(f"❌ Password reset email test error: {e}")
    
    print()
    print("✨ Email service testing completed!")

if __name__ == "__main__":
    test_email_service()