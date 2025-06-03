#!/usr/bin/env python3
"""
Test environment variable loading.
"""
import os
from decouple import config

print("🔍 Testing Environment Variable Loading")
print("=" * 50)

# Test direct environment variable access
print("📁 Direct OS environment variables:")
print(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST', 'NOT SET')}")
print(f"EMAIL_HOST_USER: {os.environ.get('EMAIL_HOST_USER', 'NOT SET')}")
print(f"EMAIL_HOST_PASSWORD: {'SET' if os.environ.get('EMAIL_HOST_PASSWORD') else 'NOT SET'}")
print()

# Test decouple config
print("🔧 Decouple config variables:")
try:
    print(f"EMAIL_HOST: {config('EMAIL_HOST', default='NOT SET')}")
    print(f"EMAIL_HOST_USER: {config('EMAIL_HOST_USER', default='NOT SET')}")
    print(f"EMAIL_HOST_PASSWORD: {'SET' if config('EMAIL_HOST_PASSWORD', default='') else 'NOT SET'}")
except Exception as e:
    print(f"Error loading config: {e}")
print()

# Check if .env file exists
env_file = '.env'
if os.path.exists(env_file):
    print(f"✅ .env file exists at: {os.path.abspath(env_file)}")
    with open(env_file, 'r') as f:
        lines = f.readlines()
    print(f"📄 .env file has {len(lines)} lines")
    
    # Check for email-related lines
    email_lines = [line.strip() for line in lines if 'EMAIL' in line and not line.strip().startswith('#')]
    print(f"📧 Found {len(email_lines)} email configuration lines:")
    for line in email_lines:
        if 'PASSWORD' in line:
            key, value = line.split('=', 1)
            print(f"   {key}={'SET' if value else 'NOT SET'}")
        else:
            print(f"   {line}")
else:
    print(f"❌ .env file not found at: {os.path.abspath(env_file)}")

print()

# Test Django settings loading
print("🐍 Testing Django settings loading...")
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinrate_api.settings')
    django.setup()
    
    from django.conf import settings
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    
except Exception as e:
    print(f"❌ Error loading Django settings: {e}")