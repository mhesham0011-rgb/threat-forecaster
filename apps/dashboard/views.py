from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.shortcuts import render
from django.utils.timezone import now
from django.views.generic import TemplateView

@login_required
def index(request):
    return render(request, "dashboard/index.html")

# Import models defensively so the dashboard still renders even if an app is missing.
try:
    from apps.audit.models import AuditEntry  # expected fields: timestamp, action, etc.
except Exception:  # pragma: no cover
    AuditEntry = None  # type: ignore

try:
    from apps.intel.models import IntelItem  # expected fields: indicator_type, ...
except Exception:  # pragma: no cover
    IntelItem = None  # type: ignore

try:
    from apps.cases.models import Case  # noqa
except Exception:  # pragma: no cover
    Case = None  # type: ignore


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

        # ---------- Time window ----------
        since_24h = now() - timedelta(hours=24)

        # ---------- KPI: Audit events in last 24h ----------
        audit_last_24h = 0
        audit_timeseries = []
        if AuditEntry is not None:
            qs_audit = AuditEntry.objects.filter(timestamp__gte=since_24h)

            audit_last_24h = qs_audit.count()

            # Build an hourly series: annotate(ts=TruncHour(...)) then values/annotate
            series = (
                qs_audit.annotate(ts=TruncHour("timestamp"))
                .values("ts")
                .annotate(count=Count("id"))
                .order_by("ts")
            )
            audit_timeseries = [
                {"ts": row["ts"].isoformat() if row["ts"] else None, "count": row["count"]}
                for row in series
            ]

        # ---------- KPI: Total intel items ----------
        intel_total = 0
        intel_top_types = []
        if IntelItem is not None:
            intel_total = IntelItem.objects.count()
            intel_top_types = list(
                IntelItem.objects.values("indicator_type")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            )
            # Normalize None types for template friendliness
            for row in intel_top_types:
                row["indicator_type"] = row["indicator_type"] or "unknown"

        # ---------- KPI: Total cases ----------
        cases_total = 0
        if Case is not None:
            try:
                cases_total = Case.objects.count()
            except Exception:
                cases_total = 0

        # ---------- Context for template ----------
        ctx.update(
            {
                # KPIs
                "kpi_audit_last_24h": audit_last_24h,
                "kpi_intel_total": intel_total,
                "kpi_cases_total": cases_total,
                # Charts / series
                "audit_timeseries": audit_timeseries,  # [{ts, count}, ...]
                "intel_top_types": intel_top_types,    # [{indicator_type, count}, ...]
            }
        )
        return ctx
