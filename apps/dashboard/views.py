from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncHour, TruncDate
from django.shortcuts import render
from django.utils.timezone import now
from django.views.generic import TemplateView

@login_required
def index(request):
    return render(request, "dashboard/index.html")

try:
    from apps.cases.models import Case
except Exception:   # fail soft if app not installed
    Case = None

try:
    from apps.ioc.models import IOC
except Exception:
    IOC = None

try:
    from apps.intel.models import IntelItem
except Exception:
    IntelItem = None

try:
    from apps.audit.models import AuditEntry
except Exception:
    AuditEntry = None


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard (executive) view:
      - KPI: Audit events in last 24h
      - KPI: Total intel items
      - KPI: Total cases
      - Chart: Audit events over last 24h, per hour
      - Chart: Intel top indicator types
    """
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ------- Cases --------
        total_cases = 0
        open_cases = 0
        cases_trend = []
        severity_breakdown = []
        top_open_cases = []
        recent_iocs = []

        if Case is not None:
            # Live counts
            total_cases = Case.objects.count()
            open_cases = Case.objects.filter(status="open").count()

            # Last 7 days trend (by opened_at)
            since_30d = now() - timedelta(days=29)
            trend_qs = (
                Case.objects.filter(opened_at__gte=since_30d)
                .annotate(day=TruncDate("opened_at"))
                .values("day")
                .annotate(total=Count("id"))
                .order_by("day")
            )
            cases_trend = [
                {"day": row["day"].strftime("%Y-%m-%d"), "total": row["total"]}
                for row in trend_qs
            ]
            top_open_cases = (
                Case.objects.filter(status="open")
                .order_by("-severity", "-opened_at")[:5]
            )

            # Severity breakdown for the donut chart
            severity_labels = {
                1: "Low",
                2: "Moderate",
                3: "High",
                4: "Critical",
            }
            sev_qs = (
                Case.objects.values("severity")
                .annotate(total=Count("id"))
                .order_by("severity")
            )
            severity_breakdown = [
                {
                    "severity": row["severity"],
                    "label": severity_labels.get(row["severity"], str(row["severity"])),
                    "total": row["total"]
                }
                for row in sev_qs
            ]

        # ---- IOC ----
        ioc_count = IOC.objects.count() if IOC is not None else 0
        if IOC is not None:
            recent_iocs = (IOC.objects.order_by("-created_at")[:5])

        # ---- INTEL LAST SYNC (best-effort) ----
        last_sync = None
        if IntelItem is not None:
            last_item = IntelItem.objects.order_by("-created_at").first()
            if last_item:
                last_sync = last_item.created_at

        # ---- AUDIT KPI: events in last 24h ----
        audit_last_24h = 0
        if AuditEntry is not None:
            since_24h = now() - timedelta(hours=24)
            audit_last_24h = AuditEntry.objects.filter(timestamp__gte=since_24h).count()

        # ---- Push into template ----
        ctx.update(
            {
                # KPIs shown at the top
                "total_cases": total_cases,
                "open_cases": open_cases,
                "ioc_count": ioc_count,

                # Data for the charts
                "cases_trend": cases_trend,
                "severity_breakdown": severity_breakdown,

                # Last intel sync timestamp
                "last_sync": last_sync,

                # Extra KPI
                "kpi_audit_last_24h": audit_last_24h,
            }
        )

        ctx["top_open_cases"] = top_open_cases
        ctx["recent_iocs"] = recent_iocs

        return ctx
