from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from .models import TwoFactorAuth, LoginAttempt
import logging

logger = logging.getLogger(__name__)

def can_send_code(user):
    """
    Check if a user can receive a new verification code (rate limiting)
    """
    cache_key = f"2fa_rate_limit_{user.id}"
    attempts = cache.get(cache_key, 0)
    
    # Allow maximum 3 code requests per 10 minutes
    if attempts >= 3:
        return False, "Too many code requests. Please wait 10 minutes before requesting again."
    
    return True, "OK"

def increment_code_request(user):
    """
    Increment the code request counter for rate limiting
    """
    cache_key = f"2fa_rate_limit_{user.id}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, 600)  # 10 minutes

def can_verify_code(user):
    """
    Check if a user can attempt code verification (rate limiting)
    """
    cache_key = f"2fa_verify_limit_{user.id}"
    attempts = cache.get(cache_key, 0)
    
    # Allow maximum 5 verification attempts per 10 minutes
    if attempts >= 5:
        return False, "Too many verification attempts. Please wait 10 minutes before trying again."
    
    return True, "OK"

def increment_verification_attempt(user):
    """
    Increment the verification attempt counter for rate limiting
    """
    cache_key = f"2fa_verify_limit_{user.id}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, 600)  # 10 minutes

def send_verification_code(user, request=None, login_attempt=True):
    """
    Generate and send a verification code to the user's email
    """
    try:
        # Check rate limiting
        can_send, message = can_send_code(user)
        if not can_send:
            logger.warning(f"Rate limit exceeded for user {user.email}")
            return False, message
        
        # Deactivate any existing unused codes for this user
        TwoFactorAuth.objects.filter(
            user=user, 
            used=False, 
            login_attempt=login_attempt
        ).update(used=True)
        
        # Generate new verification code
        code = TwoFactorAuth.generate_code()
        
        # Create new 2FA record
        two_factor_auth = TwoFactorAuth.objects.create(
            user=user,
            code=code,
            login_attempt=login_attempt
        )
        
        # Prepare email context
        context = {
            'user': user,
            'code': code,
            'expiry_minutes': 10,
            'site_name': 'Your Website',
            'login_attempt': login_attempt
        }
        
        # Send email
        subject = 'Your Security Verification Code'
        html_message = render_to_string('emails/verification_code.html', context)
        text_message = render_to_string('emails/verification_code.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Increment rate limiting counter
        increment_code_request(user)
        
        # Log the login attempt if it's for login
        if login_attempt and request:
            LoginAttempt.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                email_sent=True
            )
        
        logger.info(f"Verification code sent to {user.email}")
        return True, "Verification code sent successfully."
        
    except Exception as e:
        logger.error(f"Failed to send verification code to {user.email}: {str(e)}")
        return False, "Failed to send verification code. Please try again."

def verify_code(user, code, login_attempt=True):
    """
    Verify the provided code for the user
    """
    try:
        # Check rate limiting for verification attempts
        can_verify, message = can_verify_code(user)
        if not can_verify:
            logger.warning(f"Verification rate limit exceeded for user {user.email}")
            return False, message
        
        # Find the most recent unused code for this user
        two_factor_auth = TwoFactorAuth.objects.filter(
            user=user,
            code=code,
            used=False,
            login_attempt=login_attempt
        ).first()
        
        # Increment verification attempt counter
        increment_verification_attempt(user)
        
        if not two_factor_auth:
            return False, "Invalid verification code."
        
        if not two_factor_auth.is_valid():
            return False, "Verification code has expired."
        
        # Mark the code as used
        two_factor_auth.used = True
        two_factor_auth.save()
        
        logger.info(f"Verification code verified for {user.email}")
        return True, "Code verified successfully."
        
    except Exception as e:
        logger.error(f"Error verifying code for {user.email}: {str(e)}")
        return False, "An error occurred while verifying the code."

def get_client_ip(request):
    """
    Get the client's IP address from the request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_suspicious_activity(user, request):
    """
    Check for suspicious login activity
    """
    client_ip = get_client_ip(request)
    
    # Check recent failed attempts from this IP
    recent_attempts = LoginAttempt.objects.filter(
        ip_address=client_ip,
        success=False,
        timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    
    # Check if this is a new device/location for the user
    previous_successful_logins = LoginAttempt.objects.filter(
        user=user,
        success=True,
        ip_address=client_ip
    ).exists()
    
    return {
        'too_many_failed_attempts': recent_attempts >= 5,
        'new_device': not previous_successful_logins,
        'recent_failed_attempts': recent_attempts
    }
