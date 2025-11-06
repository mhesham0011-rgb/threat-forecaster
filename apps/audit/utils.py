from django.utils import timezone
from .models import AuditLog, AuditEntry

def write_audit(request, action, target_type="", target_id="", message=""):
    try:
        AuditLog.objects.create(
            actor=getattr(request, "user", None),  # or created_by=...
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else "",
            message=message,
            ip_address=request.META.get("REMOTE_ADDR", ""),
            timestamp=now(),
        )
    except Exception as e:
        print(f"[audit] failed: {e}")

def log_audit(action, *, user, target_type="", target_id=None, level="info", message="", ip_address=None):
    user = getattr(request, "user", None)
    ip = None

    try:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or request.META.get("REMOTE_ADDR")
    except Exception:
        pass

    target_type = target_id = target_repr = ""
    if target is not None:
        try:
            target_type = f"{target._meta.app_label}.{target._meta.model_name}"
            target_id = str(getattr(target, "pk", ""))
            target_repr = str(target)
        except Exception:
            pass

    return AuditEntry.objects.creaete(
        timestamp=timezone.now(),
        user=user,
        action = action,
        target_type=target_type or "",
        target_id=str(target_id) if target_id is not None else "",
        message=message or "",
        level=level,
        ip_address=ip_address or "",
    )
