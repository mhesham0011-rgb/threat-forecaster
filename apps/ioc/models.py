from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class IOC(models.Model):
    value = models.CharField(max_length=255)
    ioc_type = models.CharField(max_length=64)
    verdict = models.CharField(max_length=32, blank=True, default="")
    threat_score = models.IntegerField(default=0)
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen  = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    tags = models.CharField(max_length=255, blank=True, default="")

class SavedSearch(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ioc_saved_searches")
    name = models.CharField(max_length=200)
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"
