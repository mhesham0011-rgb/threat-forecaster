from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)     # e.g., 'IOC_LOOKUP','EXPORT'
    object_ref = models.CharField(max_length=256)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
