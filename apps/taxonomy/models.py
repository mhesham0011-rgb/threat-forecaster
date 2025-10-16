from django.db import models
class ATTCKTechnique(models.Model):
    tid = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=256)
    tactic = models.CharField(max_length=128)
