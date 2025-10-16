from django.db import models
from django.conf import settings

class Case(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=16, default='open')      # open/investigating/contained/closed
    severity = models.CharField(max_length=16, default='medium')  # low/medium/high/critical
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    iocs = models.ManyToManyField('ioc.IOC', blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
