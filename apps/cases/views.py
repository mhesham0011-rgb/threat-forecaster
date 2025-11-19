from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, Http404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime

from .models import Case, SavedSearch
from .forms import CaseForm

# If you use a helper to write audit logs:
from apps.audit.utils import write_audit
# If you use a model instead, import it and use AuditLog.objects.create(...)
# from apps.audit.models import AuditLog


class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "cases/index.html"
    context_object_name = "object_list"
    paginate_by = 50
    ordering = ["-opened_at"]


class CaseCreateView(LoginRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = "cases/create.html"
    success_url = reverse_lazy("cases:index")

    def form_valid(self, form):
        # Save the case first
        self.object = form.save()

        # Write audit log (don’t let failure break the request)
        try:
            write_audit(
                request=self.request,
                action="cases.create",
                message=f"Case created: {self.object}",
                target_type="cases.case",
                target_id=self.object.pk,
                extra={"level": "info"},
            )
            # If using an AuditLog model instead of helper:
            # AuditLog.objects.create(
            #     actor=self.request.user,
            #     action="cases.create",
            #     message=f"Case created: {self.object}",
            #     target_type="cases.case",
            #     target_id=self.object.pk,
            #     level="info",
            #     ip_address=getattr(self.request, "client_ip", ""),
            # )
        except Exception as e:
            print(f"[audit] failed to write log: {e}")

        messages.success(self.request, "Case created successfully.")
        return super().form_valid(form)

class CaseDetailView(DetailView):
	model = Case
	template_name = "cases/detail.html"

class CaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = "cases/update.html"
    success_url = reverse_lazy("cases:index")

    def form_valid(self, form):
        self.object = form.save()

        try:
            write_audit(
                request=self.request,
                action="cases.update",
                message=f"Case updated: {self.object}",
                target_type="cases.case",
                target_id=self.object.pk,
                extra={"level": "info"},
            )
            # Or, if using a model:
            # AuditLog.objects.create(
            #     actor=self.request.user,
            #     action="cases.update",
            #     message=f"Case updated: {self.object}",
            #     target_type="cases.case",
            #     target_id=self.object.pk,
            #     level="info",
            #     ip_address=getattr(self.request, "client_ip", ""),
            # )
        except Exception as e:
            print(f"[audit] failed to write log: {e}")

        messages.success(self.request, "Case updated successfully.")
        return super().form_valid(form)


@login_required
def case_close(request, pk):
    case = get_object_or_404(Case, pk=pk)
    case.status = "Closed"
    case.save(update_fields=["status"])

    write_audit(
        request=request,
        action="cases.close",
        message=f"Closed case '{case.title}'",
        target_type="cases.case",
        target_id=case.pk,
        extra={"status": case.status},
    )

    messages.success(request, "Case closed.")
    return redirect("cases:index")


@login_required
def case_detail_json(request, pk):
    """
    Returns JSON for a single case, used by the modal.
    GET /cases/<pk>/json/
    """
    try:
        c = Case.objects.select_related("owner").get(pk=pk)
    except Case.DoesNotExist:
        raise Http404("Case not found")

    data = {
        "id": c.id,
        "title": c.title or "",
        "summary": c.summary or "",
        "severity": c.severity,
        "severity_label": (
            c.get_severity_display()
            if hasattr(c, "get_severity_display")
            else str(c.severity)
        ),
        "status": c.status or "",
        "owner": (
            (c.owner.get_full_name() or c.owner.username)
            if getattr(c, "owner", None)
            else ""
        ),
        "opened_at": (
            localtime(c.opened_at).strftime("%Y-%m-%d %H:%M")
            if c.opened_at else ""
        ),
        "closed_at": (
            localtime(c.closed_at).strftime("%Y-%m-%d %H:%M")
            if c.closed_at else ""
        ),
    }
    return JsonResponse(data)

@login_required
def saved_search_list(request):
    searches = SavedSearch.objects.filter(owner=request.user)
    return render(request, "cases_saved_searches/list.html", {"searches": searches})

@login_required
def saved_search_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        query = request.POST.get("query")

        SavedSearch.objects.create(
            owner=request.user,
            name=name,
            query=query,
        )
        return redirect("cases_saved_search_list")

    return render(request, "cases_saved_searches/create.html")
