# Email Setup Guide for TinRate API

This guide explains how to configure Gmail SMTP for sending emails from the TinRate API.

## Overview

The TinRate API now includes a comprehensive email service that sends:
- **Verification emails** when users register
- **Welcome emails** after email verification
- **Password reset emails** for account recovery

All emails are sent from `tanguy@lytestudios.be` using Gmail's SMTP service.

## Gmail Setup Instructions

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification**
3. Follow the instructions to enable 2FA if not already enabled

### Step 2: Generate App Password

1. Go to **Security** → **2-Step Verification** → **App passwords**
2. Select **Mail** as the app and **Other** as the device
3. Enter "TinRate API" as the device name
4. Copy the generated 16-character app password (format: `xxxx xxxx xxxx xxxx`)

### Step 3: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=tanguy@lytestudios.be
EMAIL_HOST_PASSWORD=your-16-character-app-password-here
DEFAULT_FROM_EMAIL=tanguy@lytestudios.be
SERVER_EMAIL=tanguy@lytestudios.be
TINRATE_FROM_EMAIL=tanguy@lytestudios.be
TINRATE_SUPPORT_EMAIL=tanguy@lytestudios.be
```

**Important:** Replace `your-16-character-app-password-here` with the actual app password from Step 2.

## Testing Email Functionality

### Option 1: Run the Test Script

```bash
python test_email.py
```

This will test all email types without actually registering users.

### Option 2: Test via API

1. Start the Django server:
```bash
python manage.py runserver
```

2. Register a new user:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

3. Check your email for the verification code.

### Option 3: Run Unit Tests

```bash
python manage.py test authentication.tests.AuthenticationTestCase.test_user_registration_minimal_fields
```

## Email Templates

The email service includes professionally designed HTML email templates with:

- **Responsive design** that works on all devices
- **TinRate branding** with consistent styling
- **Plain text fallbacks** for email clients that don't support HTML
- **Security best practices** with proper encoding and sanitization

### Verification Email Features:
- Large, easy-to-read verification code
- 24-hour expiration notice
- Professional TinRate branding
- Support contact information

### Welcome Email Features:
- Personalized greeting
- Getting started instructions
- Direct links to dashboard and key features
- Support contact information

### Password Reset Email Features:
- Secure reset link with token
- 1-hour expiration notice
- Clear call-to-action button
- Fallback plain text link

## Troubleshooting

### Common Issues:

1. **"Authentication failed" error:**
   - Verify 2FA is enabled on the Gmail account
   - Double-check the app password is correct
   - Ensure you're using the app password, not your regular Gmail password

2. **"Connection refused" error:**
   - Check your internet connection
   - Verify EMAIL_HOST and EMAIL_PORT settings
   - Ensure EMAIL_USE_TLS is set to True

3. **Emails not being received:**
   - Check spam/junk folders
   - Verify the recipient email address is correct
   - Check Gmail's sent folder to confirm emails are being sent

4. **"Less secure app access" error:**
   - This shouldn't happen with app passwords, but if it does:
   - Use app passwords instead of regular passwords
   - Ensure 2FA is properly configured

### Debug Mode:

To see detailed email sending logs, you can temporarily switch to console backend for testing:

```python
# In settings.py or .env
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

## Security Considerations

- **Never commit** the Gmail app password to version control
- **Use environment variables** for all sensitive configuration
- **Rotate app passwords** periodically for security
- **Monitor email sending** for unusual activity
- **Use HTTPS** in production for all email links

## Production Recommendations

For production deployment, consider:

1. **Professional email service** like SendGrid, Mailgun, or AWS SES
2. **Custom domain** for from addresses (e.g., `noreply@tinrate.com`)
3. **Email analytics** and delivery monitoring
4. **Rate limiting** to prevent abuse
5. **Email templates** stored in database for easy updates

## Support

If you encounter issues with email setup:

1. Check the Django logs for detailed error messages
2. Run the test script to isolate the problem
3. Verify all environment variables are set correctly
4. Contact the development team for assistance

---

**Note:** This setup is temporary and will be replaced with a professional email service in the future.