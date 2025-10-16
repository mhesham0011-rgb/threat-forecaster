import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ThreatForecaster.settings")

app = Celery("ThreatForecaster")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()