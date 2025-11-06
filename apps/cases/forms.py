from django import forms
from .models import Case

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ["title", "severity", "status", "owner", "summary", "closed_at"]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "closed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
