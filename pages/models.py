from django.db import models
from django.contrib.auth.models import User

# This model will store all the technologies we can track
class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# This will link a User to the Technologies they use
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    technologies = models.ManyToManyField(Technology, blank=True)

    def __str__(self):
        return self.user.username

class ThreatAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vulnerability_name = models.CharField(max_length=255)
    description = models.TextField()
    date_found = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.vulnerability_name}"