from django import forms
from .models import IOC

VERDICT_CHOICES = [
    ("malicious", "Malicious"),
    ("suspicious", "Suspicious"),
    ("benign", "Benign"),
    ("unknown", "Unknown"),
]

TYPE_CHOICES = [
    ("IP Address", "IP Address"),
    ("Domain", "Domain"),
    ("File Hash", "File Hash"),
    ("URL", "URL"),
]

class IOCForm(forms.ModelForm):
    ioc_type = forms.ChoiceField(choices=TYPE_CHOICES)
    verdict = forms.ChoiceField(choices=VERDICT_CHOICES, required=False)

    class Meta:
        model = IOC
        fields = ["value", "ioc_type", "threat_score", "verdict", "first_seen"]
        widgets = {
            "first_seen": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "threat_score": forms.NumberInput(attrs={"min": 0, "max": 10, "step": 1}),
        }

