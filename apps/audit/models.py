from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model

class AuditLog(models.Model):
    # What happened
    action      = models.CharField(max_length=64)            # e.g. 'ioc.create', 'case.close'
    level       = models.CharField(max_length=16, default='info')  # info|warning|error|critical
    message     = models.TextField(blank=True, default='')   # human readable

    # Who did it
    actor       = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='audit_logs'
    )
    actor_name  = models.CharField(max_length=128, blank=True, default='')  # snapshot (in case user deleted)

    # Where/from
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True, default='')

    # Target/object
    target_type = models.CharField(max_length=64, blank=True, default='')   # e.g. 'ioc', 'case', 'intel'
    target_id   = models.CharField(max_length=64, blank=True, default='')
    target_repr = models.CharField(max_length=255, blank=True, default='')

    # Extras
    extra       = models.JSONField(default=dict, blank=True)

    # When
    created_at  = models.DateTimeField(default=now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['level']),
            models.Index(fields=['target_type']),
        ]

    def __str__(self):
        who = self.actor_name or (self.actor.username if self.actor else 'system')
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} {self.action}"

User = get_user_model()

class AuditEntry(models.Model):
    ACTION_MAX_LENGTH = 100
    TARGET_TYPE_MAX_LENGTH = 100

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=ACTION_MAX_LENGTH)
    target_type = models.CharField(max_length=TARGET_TYPE_MAX_LENGTH, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    target_repr = models.TextField(blank=True)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    extra = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        who = self.user.username if self.user else "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.action} (user={who})"
