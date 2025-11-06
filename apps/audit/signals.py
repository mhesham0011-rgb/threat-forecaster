from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .utils import AuditLog


@receiver(user_logged_in)
def _on_login(sender, user, request, **kwargs):
    AuditLog(
        user=user,
        action="auth.login",
        message="User logged in",
        level="info",
        ip_address=getattr(request, "client_ip", ""),
        target_type="auth",
    )


@receiver(user_logged_out)
def _on_logout(sender, user, request, **kwargs):
    AuditLog(
        user=user,
        action="auth.logout",
        message="User logged out",
        level="info",
        ip_address=getattr(request, "client_ip", ""),
        target_type="auth",
    )


@receiver(user_login_failed)
def _on_login_failed(sender, credentials, request, **kwargs):
    username = "<unknown>"
    try:
        # credentials is a dict; guard just in case
        username = (credentials or {}).get("username") or "<unknown>"
    except Exception:
        pass

    AuditLog(
        user=None,  # no user object on failed login
        action="auth.login_failed",
        message=f"Login failed for: {username}",
        level="warning",
        ip_address=getattr(request, "client_ip", ""),
        target_type="auth",
    )
