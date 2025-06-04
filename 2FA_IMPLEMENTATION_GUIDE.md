# Two-Factor Authentication (2FA) Implementation Guide

## 🛡️ Overview

This Django application implements a comprehensive Two-Factor Authentication (2FA) system that enhances security by requiring users to verify their identity using verification codes sent to their email addresses during login attempts.

## ✨ Features

### Core 2FA Features
- **Email-based verification codes**: 6-digit codes sent to user's registered email
- **Code expiration**: Verification codes expire after 10 minutes
- **Anti-replay protection**: Each code can only be used once
- **Rate limiting**: Prevents abuse with configurable limits
- **Session management**: Secure handling of pending login states

### Security Features
- **Suspicious activity detection**: Monitors for unusual login patterns
- **IP address tracking**: Logs and monitors login attempts by IP
- **Rate limiting**: Protects against brute force attacks
- **Admin security dashboard**: Real-time monitoring interface
- **Comprehensive logging**: Detailed audit trail of all authentication events

### User Experience Features
- **Modern dark-themed UI**: Professional and user-friendly interface
- **Auto-submit codes**: Automatic form submission when 6 digits are entered
- **Resend functionality**: AJAX-powered code resending with cooldown
- **Real-time validation**: Immediate feedback on code entry
- **Mobile responsive**: Works perfectly on all device sizes

## 🚀 Quick Start

### 1. Environment Setup

Ensure your `.env` file contains the following email configuration:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# 2FA Configuration
TWO_FACTOR_ENABLED=True
TWO_FACTOR_CODE_LENGTH=6
TWO_FACTOR_CODE_EXPIRY_MINUTES=10
```

### 2. Database Migration

Run the migrations to set up the 2FA database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser

Create an admin user to access the security dashboard:

```bash
python manage.py createsuperuser
```

### 4. Start the Server

```bash
python manage.py runserver
```

## 📋 Usage

### For Users

1. **Login Process**:
   - Navigate to `/login/`
   - Enter username and password
   - Check email for 6-digit verification code
   - Enter code on verification page
   - Access granted upon successful verification

2. **Code Resending**:
   - Click "Resend Code" if not received
   - Wait for 60-second cooldown between requests
   - Check spam folder if code doesn't arrive

### For Administrators

1. **Security Dashboard**:
   - Access `/admin/security/` (requires staff privileges)
   - Monitor real-time login attempts
   - View suspicious activity alerts
   - Track 2FA usage statistics

2. **Django Admin**:
   - Access `/admin/` to manage 2FA records
   - View `TwoFactorAuth` model for code history
   - Monitor `LoginAttempt` model for security analysis

## 🔧 Configuration

### Settings Configuration

The following settings control 2FA behavior:

```python
# mysite/settings.py

# 2FA Settings
TWO_FACTOR_ENABLED = config('TWO_FACTOR_ENABLED', default=True, cast=bool)
TWO_FACTOR_CODE_LENGTH = config('TWO_FACTOR_CODE_LENGTH', default=6, cast=int)
TWO_FACTOR_CODE_EXPIRY_MINUTES = config('TWO_FACTOR_CODE_EXPIRY_MINUTES', default=10, cast=int)

# Email Settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yoursite.com')
```

### Rate Limiting Configuration

Default rate limits (can be customized in `two_factor_utils.py`):
- **Code requests**: 3 requests per 10 minutes per user
- **Verification attempts**: 5 attempts per 10 minutes per user

## 📁 File Structure

```
main/
├── models.py                 # TwoFactorAuth and LoginAttempt models
├── forms.py                  # 2FA-related forms
├── views.py                  # Authentication views
├── two_factor_utils.py       # Core 2FA utility functions
├── admin.py                  # Django admin configuration
├── urls.py                   # URL routing
├── templates/
│   ├── auth/
│   │   └── verify_2fa.html   # 2FA verification page
│   ├── emails/
│   │   ├── verification_code.html  # HTML email template
│   │   └── verification_code.txt   # Text email template
│   └── admin/
│       └── security_dashboard.html # Security monitoring dashboard
└── migrations/
    └── 0002_twofactorauth_loginattempt.py  # Database migrations
```

## 🔍 Database Models

### TwoFactorAuth Model

Stores verification codes with the following fields:
- `user`: Foreign key to User model
- `code`: 6-digit verification code
- `created_at`: Timestamp of code generation
- `used`: Boolean flag for code usage
- `login_attempt`: Boolean flag for login vs other uses

### LoginAttempt Model

Tracks login attempts with the following fields:
- `user`: Foreign key to User model (nullable)
- `ip_address`: Client IP address
- `user_agent`: Browser user agent string
- `success`: Boolean flag for attempt success
- `email_sent`: Boolean flag for 2FA email status
- `created_at`: Timestamp of attempt

## 🛠️ API Reference

### Core Functions

#### `send_verification_code(user, request=None, login_attempt=True)`
Generates and sends a verification code to the user's email.

**Parameters:**
- `user`: Django User instance
- `request`: HTTP request object (optional)
- `login_attempt`: Boolean flag for login context

**Returns:**
- `(True, message)`: Success with message
- `(False, message)`: Failure with error message

#### `verify_code(user, code, login_attempt=True)`
Verifies a submitted verification code.

**Parameters:**
- `user`: Django User instance
- `code`: 6-digit verification code string
- `login_attempt`: Boolean flag for login context

**Returns:**
- `(True, message)`: Verification successful
- `(False, message)`: Verification failed with reason

#### `check_suspicious_activity(user, request)`
Analyzes login patterns for suspicious activity.

**Returns:**
Dictionary with:
- `too_many_failed_attempts`: Boolean
- `new_device`: Boolean
- `recent_failed_attempts`: Integer count

### Rate Limiting Functions

#### `can_send_code(user)`
Checks if user can request a new verification code.

#### `can_verify_code(user)`
Checks if user can attempt code verification.

## 🔒 Security Features

### Anti-Abuse Measures
- **Rate limiting**: Prevents rapid code generation/verification
- **Code expiration**: Limits window of opportunity for attacks
- **One-time use**: Prevents replay attacks
- **IP tracking**: Monitors for suspicious patterns

### Monitoring & Alerts
- **Real-time dashboard**: Live monitoring of authentication events
- **Suspicious activity detection**: Automated pattern recognition
- **Comprehensive logging**: Detailed audit trails
- **Admin notifications**: Alert system for security events

### Data Protection
- **Secure sessions**: Temporary storage of pending login states
- **Encrypted storage**: Secure handling of sensitive data
- **Auto-cleanup**: Automatic removal of expired codes
- **Privacy protection**: Masked email display to users

## 🧪 Testing

### Manual Testing

1. **Basic Flow**:
   - Create test user account
   - Attempt login
   - Verify email delivery
   - Test code entry and validation

2. **Edge Cases**:
   - Expired code handling
   - Invalid code submission
   - Rate limiting behavior
   - Session timeout handling

3. **Security Testing**:
   - Brute force protection
   - Code reuse prevention
   - Session security validation

### Automated Testing

```python
# Example test cases
def test_2fa_code_generation():
    # Test code generation and email sending
    pass

def test_code_verification():
    # Test valid and invalid code verification
    pass

def test_rate_limiting():
    # Test rate limiting functionality
    pass

def test_suspicious_activity_detection():
    # Test security monitoring
    pass
```

## 🚀 Production Deployment

### Email Configuration

For production, configure proper SMTP settings:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-production-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Security Considerations

1. **Environment Variables**: Never commit sensitive data to version control
2. **HTTPS**: Always use HTTPS in production
3. **Session Security**: Configure secure session cookies
4. **Database Security**: Use encrypted database connections
5. **Rate Limiting**: Implement additional rate limiting at reverse proxy level

### Monitoring

1. **Log Monitoring**: Set up log aggregation and monitoring
2. **Alert System**: Configure alerts for suspicious activity
3. **Performance Monitoring**: Monitor email delivery and response times
4. **Backup Strategy**: Regular backups of authentication logs

## 🐛 Troubleshooting

### Common Issues

#### CSRF Verification Failed
- **Cause**: Missing or invalid CSRF tokens
- **Solution**: Ensure templates include `{% csrf_token %}` and AJAX requests include proper headers

#### Email Not Delivered
- **Cause**: SMTP configuration or email provider issues
- **Solution**: Check SMTP settings, verify email credentials, check spam folders

#### Code Expired
- **Cause**: User waited too long to enter code
- **Solution**: Request new code using resend functionality

#### Rate Limiting Triggered
- **Cause**: Too many requests in short timeframe
- **Solution**: Wait for cooldown period to expire

### Debug Settings

For development debugging:

```python
# Enable detailed logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'main.two_factor_utils': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📈 Future Enhancements

### Potential Improvements
- **SMS support**: Add SMS-based code delivery
- **TOTP integration**: Support for authenticator apps
- **Backup codes**: Generate one-time backup codes
- **Device trust**: Remember trusted devices
- **Advanced analytics**: Enhanced security analytics
- **Multi-language support**: Internationalization

### Integration Options
- **Social login**: Integration with OAuth providers
- **SSO support**: Single Sign-On integration
- **API authentication**: 2FA for API endpoints
- **Mobile apps**: Native mobile app integration

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Django documentation for authentication
3. Check email provider documentation for SMTP settings
4. Review server logs for detailed error information

## 📄 License

This 2FA implementation is provided as-is for educational and development purposes. Ensure proper security review before production deployment.

---

**Last Updated**: June 2025  
**Django Version**: 4.2+  
**Python Version**: 3.8+
