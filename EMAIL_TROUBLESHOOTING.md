# Email Issue Resolution Guide

## 🔍 Problem Identified

The TinRate API email system has two issues:

### 1. ✅ Environment Variable Loading (FIXED)
- **Issue**: Django wasn't loading email settings from `.env` file
- **Cause**: System environment variables were overriding `.env` file values
- **Solution**: Set environment variables explicitly before running Django

### 2. ❌ Gmail Authentication (NEEDS FIXING)
- **Issue**: Gmail SMTP authentication failing
- **Error**: `Username and Password not accepted`
- **Cause**: App password is incorrect, expired, or 2FA not properly configured

## 🔧 Immediate Fix Required

### Step 1: Verify Gmail 2FA Setup
1. Go to https://myaccount.google.com/security
2. Ensure **2-Step Verification** is **ENABLED** for `tanguy@lytestudios.be`
3. If not enabled, enable it now

### Step 2: Generate New App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other** as the device
4. Enter "TinRate API" as the device name
5. Copy the generated 16-character password (format: `xxxx xxxx xxxx xxxx`)

### Step 3: Update Environment Configuration
Replace the current password in `.env` file:
```bash
EMAIL_HOST_PASSWORD=your-new-16-character-app-password-here
```

### Step 4: Test the Configuration
Run this command to test with the new password:
```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend && \
export EMAIL_HOST=smtp.gmail.com && \
export EMAIL_HOST_USER=tanguy@lytestudios.be && \
export EMAIL_HOST_PASSWORD=your-new-app-password && \
python test_gmail_connection.py
```

## 🚀 Permanent Solution

### Option A: Fix Current Setup
1. Generate new Gmail app password (steps above)
2. Update `.env` file with new password
3. Restart Django server with environment variables set

### Option B: Use Environment Variables (Recommended)
Instead of relying on `.env` file loading, set environment variables directly:

```bash
# Add to your server startup script or .bashrc
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=tanguy@lytestudios.be
export EMAIL_HOST_PASSWORD=your-app-password-here
export TINRATE_FROM_EMAIL=tanguy@lytestudios.be
export TINRATE_SUPPORT_EMAIL=tanguy@lytestudios.be
```

## 🧪 Testing Commands

### Test Gmail Connection
```bash
python test_gmail_connection.py
```

### Test Registration with Email
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

## 📧 Expected Results After Fix

When working correctly, you should see:
1. ✅ SMTP connection successful
2. ✅ Django email sent successfully
3. ✅ TinRate email service working
4. 📬 Actual emails received in inbox

## 🔒 Security Notes

- **Never commit** app passwords to version control
- **Rotate app passwords** regularly for security
- **Use environment variables** in production
- **Monitor email sending** for unusual activity

## 🆘 If Still Not Working

1. **Check Gmail Account**: Ensure the account is not locked or suspended
2. **Try Different Password**: Generate a completely new app password
3. **Check Firewall**: Ensure port 587 is not blocked
4. **Test with Different Email**: Try with a different Gmail account temporarily

## 📞 Next Steps

1. Generate new Gmail app password
2. Update `.env` file or set environment variables
3. Test with `python test_gmail_connection.py`
4. Test registration endpoint
5. Verify emails are received

The code implementation is correct - this is purely a Gmail authentication configuration issue.