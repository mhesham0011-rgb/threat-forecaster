import json

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.http import require_GET, require_POST

from rest_framework import generics, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from .models import Tactic, Technique, TechniqueStat, CTIEvent, DetectionRule, TaxonomyTerm, SyncStatus, TaxonomyRefreshRun
from .serializers import TacticSerializer, TechniqueListSerializer,TechniqueDetailSerializer, CTIEventSerializer, DetectionRuleSerializer

@require_GET
def live_summary(request):
    # Latest run
    latest = TaxonomyRefreshRun.objects.order_by("-started_at").first()
    if latest:
        ts = latest.finished_at or latest.started_at
    else:
        ts = None

    def iso(v):
        return v.isoformat() if v else None

    # Basic timestamps for the existing badges
    data = {
        "attack_last_success": iso(ts),
        "cti_last_success": iso(ts),
        "coverage_last_success": iso(ts),
    }

    # Latest run status
    if latest:
        data.update({
            "last_run_started": iso(latest.started_at),
            "last_run_finished": iso(latest.finished_at),
            "last_run_success": latest.success,
            "last_run_error": (latest.error_message or "")[:400],
            "last_run_new_count": len(latest.new_attack_ids or []),
        })
    else:
        data.update({
            "last_run_started": None,
            "last_run_finished": None,
            "last_run_success": False,
            "last_run_error": "",
            "last_run_new_count": 0,
        })

    # New techniques in last 24h
    since = now() - timedelta(hours=24)
    recent_runs = TaxonomyRefreshRun.objects.filter(started_at__gte = since, success=True)

    new_ids_24h = sorted({tid for r in recent_runs for tid in (r.new_attack_ids or [])})

    data["new_attack_ids_24h"] = new_ids_24h
    data["new_attack_count_24h"] = len(new_ids_24h)

    return JsonResponse(data)

def taxonomy_index(request):
    """
    HTML Taxonomy page. This helps the navbar to link to.
    """

    return render(request, "taxonomy/index.html")

@login_required
@require_POST
def taxonomy_delete(request):
    term_id = request.POST.get("id")

    return JsonResponse({"ok": True})

@require_GET
@login_required
def taxonomy_list(request):
    """
    Return list of terms as JSON.
    Accepts:
      - ?vocab=...   (required: which group to show)
      - ?q=...       (optional: search in key/label)
    Response:
      { "rows": [ {id, vocab, key, label, order, color, enabled}, ... ] }
    """
    vocab = request.GET.get("vocab")
    q = request.GET.get("q", "").strip()

    qs = TaxonomyTerm.objects.all()
    if vocab:
        qs = qs.filter(vocab=vocab)

    if q:
        from django.db.models import Q
        qs = qs.filter(Q(key__icontains=q) | Q(label__icontains=q))

    rows = [
        {
            "id": t.id,
            "vocab": t.vocab,
            "key": t.key,
            "label": t.label,
            "order": t.order,
            "color": t.color,
            "enabled": t.enabled,
        }
        for t in qs
    ]
    return JsonResponse({"rows": rows})

@require_POST
@login_required
def taxonomy_save(request):
    """
    Create or update a term from form data.

    Expects POST fields:
      - id (optional; if provided, update, else create)
      - vocab
      - key
      - label
      - order
      - color
      - enabled (on/off checkbox)
    Returns: { "ok": true, "id": <id> } or { "ok": false, "error": "..." }
    """
    term_id = request.POST.get("id")
    vocab = (request.POST.get("vocab") or "").strip()
    key = (request.POST.get("key") or "").strip()
    label = (request.POST.get("label") or "").strip()
    color = (request.POST.get("color") or "").strip()
    enabled = request.POST.get("enabled") in ("on", "true", "1")

    # order might be empty
    try:
        order = int(request.POST.get("order") or 0)
    except ValueError:
        order = 0

    if not vocab or not key:
        return JsonResponse(
            {"ok": False, "error": "vocab and key are required"}, status=400
        )

    if term_id:
        # update existing
        try:
            term = TaxonomyTerm.objects.get(id=term_id)
        except TaxonomyTerm.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": "Term not found"}, status=404
            )
    else:
        # create new
        term = TaxonomyTerm(vocab=vocab, key=key)

    term.label = label
    term.order = order
    term.color = color
    term.enabled = enabled
    term.vocab = vocab  # in case you allow changing vocab on edit
    term.key = key      # in case you allow changing key
    term.save()

    return JsonResponse({"ok": True, "id": term.id})

class CTIEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view of CTI events / reports, with filters.
    """
    queryset = CTIEvent.objects.all().order_by("-published_at")
    serializer_class = CTIEventSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        "source": ["exact"],                              # ?source=MISP
        "techniques__attack_id": ["exact"],              # ?techniques__attack_id=T1059
        "published_at": ["date__gte", "date__lte"],      # ?published_at__date__gte=2025-11-01
    }

    search_fields = ["title", "summary", "external_id"]
    ordering_fields = ["published_at", "source", "title"]
    ordering = ["-published_at"]

class DetectionRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to mapped detection rules.
    """
    queryset = DetectionRule.objects.select_related("technique").all()
    serializer_class = DetectionRuleSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        "technique__attack_id": ["exact"],      # ?technique__attack_id=T1059
        "source_system": ["exact"],            # ?source_system=Wazuh
        "enabled": ["exact"],
    }

    search_fields = ["name", "rule_id", "description", "technique__attack_id"]
    ordering_fields = ["source_system", "name", "last_tested"]
    ordering = ["source_system", "name"]


class TacticListView(generics.ListAPIView):
    """
    For building the ATT&CK matrix on the Taxonomy page.
    """
    queryset = Tactic.objects.all().order_by("order")
    serializer_class = TacticSerializer

class TacticViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to tactics and their techniques.
    Used to build the ATT&CK matrix columns.
    """

    queryset = Tactic.objects.all().order_by("order")
    serializer_class = TacticSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["attack_id", "name", "description"]
    ordering_fields = ["order", "attack_id", "name"]
    ordering = ["order"]

class TechniqueListView(generics.ListAPIView):
    """
    Optional: list techniques independently of tactics.
    """
    queryset = Technique.objects.select_related("tactic").all()
    serializer_class = TechniqueListSerializer


class TechniqueDetailView(generics.RetrieveAPIView):
    """
    Full detail of a single technique, including live stats + detections + CTI.
    """
    lookup_field = "attack_id"
    queryset = Technique.objects.select_related("tactic").all()
    serializer_class = TechniqueDetailSerializer


class TechniqueStatsSummaryView(APIView):
    """
    Lightweight summary for dashboards / heatmaps.
    Returns aggregated stats for all techniques.
    """

    def get(self, request, *args, **kwargs):
        stats = TechniqueStat.objects.select_related("technique", "technique__tactic")
        data = []

        for s in stats:
            data.append(
                {
                    "attack_id": s.technique.attack_id,
                    "technique_name": s.technique.name,
                    "tactic_attack_id": s.technique.tactic.attack_id,
                    "sightings_7d": s.sightings_7d,
                    "sightings_30d": s.sightings_30d,
                    "last_seen": s.last_seen,
                    "coverage_score": s.coverage_score,
                }
            )

        return Response(
            {
                "generated_at": now(),
                "techniques": data,
            }
        )

class TechniqueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to ATT&CK techniques, with filters.
    """
    queryset = (
        Technique.objects.select_related("tactic")
        .prefetch_related("stats")
        .all()
    )

    # Default list serializer (lightweight)
    serializer_class = TechniqueListSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filter by related fields
    filterset_fields = {
        "tactic__attack_id": ["exact"],      # ?tactic__attack_id=TA0001
        "tactic__name": ["exact", "icontains"],
        "platforms": ["icontains"],          # If you store platforms as JSON list
        "is_deprecated": ["exact"],
    }

    search_fields = [
        "attack_id",
        "name",
        "description",
        "tactic__attack_id",
        "tactic__name",
    ]

    ordering_fields = ["attack_id", "name", "tactic__order"]
    ordering = ["tactic__order", "attack_id"]

    def get_serializer_class(self):
        """
        Use a richer serializer for retrieve() calls.
        """
        if self.action == "retrieve":
            return TechniqueDetailSerializer
        return TechniqueListSerializer

    lookup_field = "attack_id"  # so /techniques/T1059/

    @action(detail=False, methods=["get"])
    def stats(self, request, *args, **kwargs):
        """
        /api/taxonomy/techniques/stats/
        Lightweight stats summary for dashboards / heatmaps.
        """
        stats = TechniqueStat.objects.select_related("technique", "technique__tactic")

        # Optional: filtering by tactic via query param
        tactic_id = request.query_params.get("tactic")
        if tactic_id:
            stats = stats.filter(technique__tactic__attack_id=tactic_id)

        data = [
            {
                "attack_id": s.technique.attack_id,
                "technique_name": s.technique.name,
                "tactic_attack_id": s.technique.tactic.attack_id,
                "tactic_name": s.technique.tactic.name,
                "sightings_7d": s.sightings_7d,
                "sightings_30d": s.sightings_30d,
                "last_seen": s.last_seen,
                "coverage_score": s.coverage_score,
            }
            for s in stats
        ]

        return Response(
            {
                "generated_at": now(),
                "count": len(data),
                "results": data,
            }
        )

ATTACK_VOCAB = "attack.technique"


def run_live_refresh(what=None):
    """
    Does the ATT&CK / CTI / coverage sync, then mirrors Techniques into
    TaxonomyTerm so the Taxonomy UI can show latest techniques.
    Returns a stats dict for logging.
    """

    with transaction.atomic():
        # ---- SNAPSHOT TAXONOMY STATE BEFORE SYNC ----
        before_ids = set(
            TaxonomyTerm.objects
            .filter(vocab=ATTACK_VOCAB)
            .values_list("key", flat=True)
        )

        # ---- YOUR EXISTING SYNC LOGIC HERE (optional) ----
        # e.g.:
        #   sync_attack()
        #   sync_cti()
        #   recompute_coverage()
        # --------------------------------------------------

        # ---- MIRROR Technique → TaxonomyTerm ----

        # Existing terms for this vocab, keyed by ATT&CK ID
        existing_terms = {
            t.key: t
            for t in TaxonomyTerm.objects.filter(vocab=ATTACK_VOCAB)
        }

        # For each Technique in the DB, ensure there is a matching TaxonomyTerm
        for tech in Technique.objects.select_related("tactic").all():
            key = tech.attack_id
            label = tech.name

            # Use tactic.order to group techniques roughly by tactic
            order = tech.tactic.order if getattr(tech, "tactic_id", None) else 0
            color = "info"
            enabled = not tech.is_deprecated

            term = existing_terms.pop(key, None)

            if term is None:
                # New term
                TaxonomyTerm.objects.create(
                    vocab=ATTACK_VOCAB,
                    key=key,
                    label=label,
                    order=order,
                    color=color,
                    enabled=enabled,
                )
            else:
                # Update existing term if anything changed
                changed = False
                if term.label != label:
                    term.label = label
                    changed = True
                if term.order != order:
                    term.order = order
                    changed = True
                if term.color != color:
                    term.color = color
                    changed = True
                if term.enabled != enabled:
                    term.enabled = enabled
                    changed = True
                if changed:
                    term.save()

        # Anything left in existing_terms is a key that no longer exists as a Technique
        removed_keys = list(existing_terms.keys())
        if removed_keys:
            TaxonomyTerm.objects.filter(
                vocab=ATTACK_VOCAB,
                key__in=removed_keys,
            ).update(enabled=False)

        # ---- DIFF AFTER SYNC (for logs / status panel) ----
        after_ids = set(
            TaxonomyTerm.objects
            .filter(vocab=ATTACK_VOCAB)
            .values_list("key", flat=True)
        )

        new_ids = sorted(after_ids - before_ids)
        removed_ids = sorted(before_ids - after_ids)

    # Return stats for TaxonomyRefreshRun + /live/summary/
    return {
        "scope": what or "all",
        "new_attack_ids": new_ids,
        "removed_attack_ids": removed_ids,
    }

ATTACK_VOCAB = "attack.technique"  # you already have this above run_live_refresh


def taxonomy_terms_api(request):
    """
    Lightweight JSON API for the Taxonomy table.
    Returns TaxonomyTerm rows for a given vocab (default: ATT&CK techniques).
    Shape matches what the front-end expects: {"rows": [...]}.
    """
    vocab = request.GET.get("vocab") or ATTACK_VOCAB
    q = (request.GET.get("q") or "").strip()

    qs = TaxonomyTerm.objects.filter(vocab=vocab)

    if q:
        qs = qs.filter(
            Q(key__icontains=q) |
            Q(label__icontains=q)
        )

    rows = [
        {
            "id": t.id,
            "key": t.key,
            "label": t.label,
            "order": t.order,
            "color": t.color,
            "enabled": t.enabled,
        }
        for t in qs.order_by("order", "key")
    ]

    return JsonResponse({"rows": rows})

@require_POST
@login_required
def live_refresh(request):
	"""
	Called by the 'Refresh now' button in the UI.
	"""

	payload = json.loads(request.body or "{}")
	what = payload.get("what")  # 'cti', 'attack', etc. or None
	stats = run_live_refresh(what=what)

	return JsonResponse({"ok": True, "stats":stats})
