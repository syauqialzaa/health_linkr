from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime
from health_linkr_app.models import SessionLog

class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get or create session log for this session
            session_id = request.session.session_key or ''
            session_log = SessionLog.objects.filter(
                user=request.user,
                session_id=session_id,
                logout_time__isnull=True
            ).first()

            # Force logout if session is marked as expired
            if session_log and session_log.is_expired:
                logout(request)
                return self.get_response(request)

            if not session_log and session_id:
                # Create new session log if none exists
                session_log = SessionLog.objects.create(
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    session_id=session_id
                )

            if session_log:
                # Check for session expiration
                last_activity = request.session.get('last_activity')
                if last_activity:
                    last_activity_dt = datetime.fromtimestamp(last_activity, tz=timezone.get_current_timezone())
                    if (timezone.now() - last_activity_dt).total_seconds() > 1800:  # 30 minutes
                        # Mark session as expired
                        session_log.is_expired = True
                        session_log.logout_time = timezone.now()
                        session_log.save()
                        logout(request)
                    else:
                        # Update last activity
                        request.session['last_activity'] = timezone.now().timestamp()

        response = self.get_response(request)
        return response

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and request.session.session_key:
        # Mark existing session as logged out
        SessionLog.objects.filter(
            user=user,
            session_id=request.session.session_key,
            is_expired=False,
            logout_time__isnull=True
        ).update(
            logout_time=timezone.now(),
            is_expired=True
        )

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Create new session log on login
    if user and request.session.session_key:
        SessionLog.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key
        )

@receiver(post_save, sender=SessionLog)
def handle_session_expiry(sender, instance, **kwargs):
    """Handle forced session expiry by admin"""
    if instance.is_expired and instance.session_id and not instance.logout_time:
        from django.contrib.sessions.models import Session
        try:
            # Delete the session to force logout
            Session.objects.filter(session_key=instance.session_id).delete()
            # Update logout time
            instance.logout_time = timezone.now()
            instance.save()
        except Session.DoesNotExist:
            pass
