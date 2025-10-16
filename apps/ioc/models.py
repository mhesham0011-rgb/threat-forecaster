from django.db import models
from simple_history.models import HistoricalRecords

class IOC(models.Model):
    TYPE_CHOICES=[("ip","IP"),("domain","Domain"),("url","URL"),("sha256","SHA256")]
    value = models.CharField(max_length=512, unique=True, db_index=True)
    ioc_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    verdict = models.CharField(max_length=16, default="unknown")
    threat_score = models.FloatField(default=0.0)
    tags = models.JSONField(default=list, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen  = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

class Enrichment(models.Model):
    ioc = models.ForeignKey(IOC, on_delete=models.CASCADE, related_name="enrichments")
    source = models.CharField(max_length=64)
    payload = models.JSONField()
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
