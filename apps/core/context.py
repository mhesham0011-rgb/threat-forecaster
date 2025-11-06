from django.utils import timezone

# This function will be called on every request to inject common data into templates
def globals(request):
    """
    Return site-wide context variables.
    Add whatever you want to be available in all templates.
    """
    try:
        from apps.cases.models import Case
        from apps.intel.models import IntelItem
    except Exception:
        Case = None
        IntelItem = None

    total_cases = Case.objects.count() if Case else 0
    open_cases = Case.objects.filter(status__in=["open", "new"]).count() if Case else 0
    last_intel = (
        IntelItem.objects.order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
        if IntelItem
        else None
    )

    return {
        "APP_TITLE": "Threat Forecaster",
        "NOW": timezone.now(),
        "NAV_TOTAL_CASES": total_cases,
        "NAV_OPEN_CASES": open_cases,
        "NAV_LAST_INTEL_SYNC": last_intel,
    }
