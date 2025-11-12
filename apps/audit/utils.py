from django.utils import timezone
from .models import AuditLog, AuditEntry

def write_audit(request, action, target_type="", target_id="", message="", level="info", extra=None):
    """
    Minimal, safe audit writer. Does not assume extra model fields.
    """
    try:
        AuditLog.objects.create(
            actor=getattr(request, "user", None) if hasattr(request, "user") else None,
            action=action,
            level=level,
            message=message or "",
            target_type=target_type or "",
            target_id=str(target_id) if target_id is not None else "",
            ip_address=(getattr(request, "client_ip", None) or request.META.get("REMOTE_ADDR", "")) if hasattr(request, "META") else "",
            # created_at is handled by model defaults/migrations – no manual timestamp here
            # extra can be stored if your model has it; add: extra=extra
        )
    except Exception as e:
        # Never break the main flow for audit
        print(f"[audit] write_audit failed: {e}")

def write_entry(user=None, action="", target=None, target_type="", target_id=None, message="", level="info", ip_address="", extra=None):
    target_repr = ""
    if target is not None:
        try:
            target_repr = str(target)
        except Exception:
            target_repr = ""

    return AuditEntry.objects.create(
        timestamp=timezone.now(),
        user=user,
        action=action,
        target_type=target_type or "",
        target_id=str(target_id) if target_id is not None else "",
        target_repr=target_repr,
        message=message or "",
        level=level,
        ip_address=ip_address or "",
        extra=extra or None,
    )
