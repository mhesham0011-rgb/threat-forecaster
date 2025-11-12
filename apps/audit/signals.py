from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .utils import write_audit

@receiver(user_logged_in)
def _on_login(sender, user, request, **kwargs):
    write_audit(
        request=request,
        action="auth.login",
        message="User logged in",
        target_type="auth",
    )

@receiver(user_logged_out)
def _on_logout(sender, user, request, **kwargs):
    write_audit(
        request=request,
        action="auth.logout",
        message="User logged out",
        target_type="auth",
    )

@receiver(user_login_failed)
def _on_login_failed(sender, credentials, request, **kwargs):
    username = (credentials or {}).get("username") or "<unknown>"
    write_audit(
        request=request,
        action="auth.login_failed",
        message=f"Login failed for: {username}",
        target_type="auth",
    )
