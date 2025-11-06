from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.functional import SimpleLazyObject
from .models import Case
from apps.audit.utils import AuditLog

def _safe_user(instance):
    return getattr(instance, "_actor", None)

@receiver(post_save, sender=Case)
def _case_saved(sender, instance, created, **kwargs):
    user = _safe_user(instance)
    action = "case.create" if created else "case.update"
    AuditLog(user=user, action=action, level="info",
              message=f"{'Created' if created else 'Updated'} case",
              target_type="cases.case", target_id=instance.id)

@receiver(post_delete, sender=Case)
def _case_deleted(sender, instance, **kwargs):
    user = _safe_user(instance)
    AuditLog(user=user, action="case.delete", level="warning",
              message="Deleted case", target_type="cases.case",
              target_id=instance.id)
