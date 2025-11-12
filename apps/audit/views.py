from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q

from apps.audit.utils import write_audit
from .models import AuditLog, AuditEntry, SavedSearch

import csv

class AuditListView(LoginRequiredMixin, ListView):
    model = AuditEntry
    template_name = "audit/index.html"
    context_object_name = "entries"
    paginate_by = 25
    ordering = ["-timestamp"]

    def get_queryset(self):
        return AuditEntry.objects.all().order_by("-timestamp")

@login_required
def index(request):
    # server-rendered table; client uses AJAX to fetch rows
    return render(request, "audit/index.html", {})

@login_required
def list_json(request):
    """
    Lightweight JSON for DataTables: supports search & filters.
    Query params:
      q=free_text   level=info|warning|error|critical
      action=exact  actor=<username>  page=  size=
      since=YYYY-MM-DD  until=YYYY-MM-DD
    """
    qs = AuditLog.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(message__icontains=q) | qs.filter(action__icontains=q) | qs.filter(target_repr__icontains=q)

    level = request.GET.get('level')
    if level:
        qs = qs.filter(level=level)

    action = request.GET.get('action')
    if action:
        qs = qs.filter(action=action)

    actor = request.GET.get('actor')
    if actor:
        qs = qs.filter(actor_name__iexact=actor)

    since = request.GET.get('since')
    until = request.GET.get('until')
    if since:
        qs = qs.filter(created_at__date__gte=since)
    if until:
        qs = qs.filter(created_at__date__lte=until)

    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 25))
    paginator = Paginator(qs, size)
    pg = paginator.get_page(page)

    rows = []
    for a in pg.object_list:
        rows.append({
            "id": a.id,
            "time": localtime(a.created_at).strftime("%Y-%m-%d %H:%M"),
            "actor": a.actor_name or "system",
            "level": a.level.capitalize(),
            "action": a.action,
            "target": a.target_repr or f"{a.target_type}:{a.target_id}",
            "ip": a.ip_address or "",
        })

    return JsonResponse({
        "page": page,
        "pages": paginator.num_pages,
        "total": paginator.count,
        "rows": rows
    })

@login_required
def detail_json(request, pk: int):
    a = get_object_or_404(AuditLog, pk=pk)
    data = {
        "id": a.id,
        "time": localtime(a.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        "actor": a.actor_name or "system",
        "level": a.level,
        "action": a.action,
        "message": a.message,
        "target_type": a.target_type,
        "target_id": a.target_id,
        "target_repr": a.target_repr,
        "ip": a.ip_address,
        "ua": a.user_agent[:500],
        "extra": a.extra,
    }
    return JsonResponse(data)

@login_required
def export_csv(request):
    qs = AuditEntry.objects.all().order_by("-timestamp")

    # optional filters from query string
    search = request.GET.get("q")
    level = request.GET.get("level")

    if search:
        qs = qs.filter(
            Q(message__icontains=search) |
            Q(action__icontains=search) |
            Q(target_repr__icontains=search)
        )
    if level and level != "all":
        qs = qs.filter(level=level)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_log.csv"'

    writer = csv.writer(response)
    writer.writerow(["time", "level", "actor", "action", "target", "ip"])

    for e in qs:
        writer.writerow([
            e.timestamp,
            e.level,
            getattr(e.actor, "username", ""),
            e.action,
            e.target_repr or f"{e.target_type}#{e.target_id}",
            e.ip_address or "",
        ])

    return response

@login_required
def saved_search_list(request):
    searches = SavedSearch.objects.filter(owner=request.user)
    return render(request, "audit_saved_searches/list.html", {"searches": searches})

@login_required
def saved_search_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        query = request.POST.get("query")

        SavedSearch.objects.create(owner=request.user, name=name, query=query,)

        return redirect("audit_saved_search_list")

    return render(request, "audit_saved_searches/create.html")
