from django.db import models

class IOC(models.Model):
    value = models.CharField(max_length=255)
    ioc_type = models.CharField(max_length=64)
    verdict = models.CharField(max_length=32, blank=True, default="")
    threat_score = models.IntegerField(default=0)
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen  = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    tags = models.CharField(max_length=255, blank=True, default="")
