from django.db import models
from django.utils.timezone import now

class TaxonomyTerm(models.Model):
    """Generic taxonomy term used across the app."""
    VOCABS = [
        ("indicator_type", "Indicator Type"),
        ("severity",       "Severity"),
        ("confidence",     "Confidence"),
        ("case_status",    "Case Status"),
        ("intel_source",   "Intel Source"),
        ("tag",            "Tag"),
    ]

    vocab     = models.CharField(max_length=32, choices=VOCABS, db_index=True)
    key       = models.CharField(max_length=64, db_index=True)      # machine key (e.g., ip / 5 / high)
    label     = models.CharField(max_length=128)                    # human label (e.g., IP Address / Critical)
    order     = models.IntegerField(default=0)                      # for UI sorting
    color     = models.CharField(max_length=16, blank=True)         # e.g., 'danger', 'warning', 'info'
    enabled   = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("vocab", "key")]
        ordering = ("vocab", "order", "label")

    def __str__(self):
        return f"{self.vocab}:{self.key} → {self.label}"
