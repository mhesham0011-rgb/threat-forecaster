from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import TaxonomyTerm

class TaxonomyIndexView(LoginRequiredMixin, TemplateView):
    template_name = "taxonomy/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["vocabs"] = TaxonomyTerm.VOCABS
        ctx["current_vocab"] = self.request.GET.get("vocab", "indicator_type")
        return ctx

def list_terms(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "unauthorized"}, status=401)

    vocab = request.GET.get("vocab") or "indicator_type"
    q = (request.GET.get("q") or "").strip()
    qs = TaxonomyTerm.objects.filter(vocab=vocab)
    if q:
        qs = qs.filter(Q(key__icontains=q) | Q(label__icontains=q))

    data = [{
        "id": t.id,
        "key": t.key,
        "label": t.label,
        "order": t.order,
        "color": t.color or "",
        "enabled": t.enabled,
    } for t in qs.order_by("order","label")]

    return JsonResponse({"rows": data})

@require_POST
def save_term(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error":"unauthorized"}, status=401)

    payload = request.POST
    term_id = payload.get("id")
    vocab   = payload.get("vocab")
    key     = (payload.get("key") or "").strip()
    label   = (payload.get("label") or "").strip()
    order   = int(payload.get("order") or 0)
    color   = (payload.get("color") or "").strip()
    enabled = payload.get("enabled") in ("true","1","on","yes")

    if not vocab or not key or not label:
        return HttpResponseBadRequest("vocab, key, label required")

    if term_id:
        term = get_object_or_404(TaxonomyTerm, pk=term_id)
        term.key, term.label, term.order, term.color, term.enabled = key, label, order, color, enabled
        term.save()
    else:
        term = TaxonomyTerm.objects.create(
            vocab=vocab, key=key, label=label, order=order, color=color, enabled=enabled
        )
    return JsonResponse({"ok": True, "id": term.id})

@require_POST
def delete_term(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error":"unauthorized"}, status=401)
    term = get_object_or_404(TaxonomyTerm, pk=request.POST.get("id"))
    term.delete()
    return JsonResponse({"ok": True})
