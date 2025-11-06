from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Case(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    SEVERITY_CHOICES = [
        (1, "Low"),
        (2, "Moderate"),
        (3, "High"),
        (4, "Critical"),
    ]

    title = models.CharField(max_length=200)
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    summary = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return self.title
