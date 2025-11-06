from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

User = get_user_model()

class IntelItem(models.Model):
    INDICATOR_TYPES = [
        ("ip", "IP Address"),
        ("domain", "Domain"),
        ("hash", "File Hash"),
        ("url", "URL"),
        ("malware", "Malware Family"),
        ("campaign", "Campaign / Actor"),
    ]

    value = models.CharField(max_length=255)  # e.g. evil.example.com / 45.76.x.x / SHA256
    indicator_type = models.CharField(max_length=50, choices=INDICATOR_TYPES)
    severity = models.IntegerField(default=1)
    confidence = models.IntegerField(default=50)
    source = models.CharField(max_length=255, blank=True)

    description = models.TextField(blank=True)

    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
    )

    class Meta:
        ordering = ["-last_seen", "-created_at"]
        unique_together = ("value", "source")

    def __str__(self):
        return self.value

    def severity_label(self):
        return (
                "Critical" if self.severity >= 4 else
                "High" if self.severity == 3 else
                "Moderate" if self.severity == 2 else
                "Low"
        )
