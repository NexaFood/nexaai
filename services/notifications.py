"""
Notification service for sending alerts to the application owner.
"""
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def notify_owner(title, content):
    """
    Send a notification to the application owner.
    
    Args:
        title: Notification title
        content: Notification content/message
    
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        # Log the notification
        logger.info(f"Owner Notification - {title}: {content}")
        
        # Send email if configured
        if settings.OWNER_EMAIL:
            try:
                send_mail(
                    subject=f"[Manufacturing Orchestrator] {title}",
                    message=content,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
                    recipient_list=[settings.OWNER_EMAIL],
                    fail_silently=False,
                )
                logger.info(f"Email notification sent to {settings.OWNER_EMAIL}")
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to send owner notification: {e}")
        return False


def notify_user(user, title, message):
    """
    Send a notification to a specific user.
    
    Args:
        user: User object
        title: Notification title
        message: Notification message
    
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        logger.info(f"User Notification to {user.username} - {title}: {message}")
        
        # Send email if user has email
        if user.email:
            try:
                send_mail(
                    subject=f"[Manufacturing Orchestrator] {title}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info(f"Email notification sent to {user.email}")
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to send user notification: {e}")
        return False
