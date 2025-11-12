import os
import requests
import logging

from datetime import datetime
from collections import Counter
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.utils.timezone import make_aware
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import IntelItem, SavedSearch
from apps.audit.utils import write_audit

logger = logging.getLogger(__name__)

def _require_env(var):
    val = os.environ.get(var)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return val

def parse_timestamp(ts):
    """
    Try to turn an API timestamp string into a timezone-aware 
    Python datetime. If it fails, return None.
    """

    if not ts:
         return None

    # If it's already a datetime (some sources actually return that), accept it.
    if isinstance(ts, datetime):
        # ensure it's aware
        return ts if ts.tzinfo else make_aware(ts, timezone=timezone.utc)

    # Try a couple common formats.
    candidates = [
        "%Y-%m-%d %H:%M:%S",      # '2025-10-28 15:12:00'
        "%Y-%m-%d %H:%M",         # '2025-10-28 15:12'
        "%Y-%m-%dT%H:%M:%SZ",     # '2025-10-28T15:12:00Z'
        "%Y-%m-%dT%H:%M:%S.%fZ",  # '2025-10-28T15:12:00.123Z'
        "%Y-%m-%dT%H:%M:%S%z",    # '2025-10-28T15:12:00+00:00'
    ]

    for fmt in candidates:
        try:
            dt = datetime.strptime(str(ts), fmt)
            # Attach UTC if naive
            if dt.tzinfo is None:
                dt = make_aware(dt, timezone = timezone.utc)
            return dt
        except ValueError:
            continue

    # Couldn't parse
    return None

def map_severity_to_score(sev_label):
    """
    Normalize severity into a 1–5 numeric score.

    Handles both:
    - string labels ("critical", "high", etc.)
    - direct numbers (5, 4, 3...)
    """
    if sev_label is None:
        return 1  # default low

    if isinstance(sev_label, (int, float)):
        try:
            n = int(sev_label)
        except ValueError:
            n = 1
        # clamp to [1,5] just in case
        return max(1, min(n, 5))

    # Otherwise treat it as text
    sev_text = str(sev_label).lower().strip()

    if sev_text in ("critical", "malicious", "blacklist", "block", "high", "severe"):
        return 5
    if sev_text in ("medium", "moderate", "suspicious", "elevated"):
        return 3
    if sev_text in ("low", "info", "informational", "benign"):
        return 1

    # unknown label -> default middle-ish
    return 3

def map_confidence_to_score(val):
    """
    Normalize confidence to an integer 0-100 for storage.
    Handles:
      - numeric strings like "80"
      - ints like 80
      - words like 'High', 'Medium', 'Low'
    """
    if val is None:
        return 0

    # If it's already a number (e.g. 80 or "80")
    try:
        return int(val)
    except (TypeError, ValueError):
        pass

    # If it's a label like "High", "Low", "Medium"
    label = str(val).strip().lower()
    if label in ("high", "very high", "critical"):
        return 90
    if label in ("medium", "moderate"):
        return 60
    if label in ("low", "unknown", "info", "informational"):
        return 30

    # default fallback
    return 50

def severity_label(num):
    """
    Turn numeric severity (1-4) into a human label.
    """
    num = int(num)
    return (
        "Critical" if num == 4 else
        "High" if num == 3 else
        "Moderate" if num == 2 else
        "Low"
    )


class IntelListView(ListView):
    """
    Show all intel in a table.
    Uses template: templates/intel/index.html
    Context: object_list = queryset of IntelItem
    """
    model = IntelItem
    template_name = "intel/index.html"
    context_object_name = "object_list"
    ordering = ["-first_seen"]

    # force auth like you did with @login_required before
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # redirect to login if anonymous
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


@require_POST
@login_required
def intel_create(request):
    """
    Handle POST from the Add Intel modal.
    If it's an AJAX request, return JSON for the new row.
    Otherwise, just return 400.
    """

    value = request.POST.get('value', '').strip()
    indicator_type = request.POST.get('indicator_type', '').strip()
    severity_raw = request.POST.get('severity', '').strip()
    confidence = request.POST.get('confidence', '').strip()
    source = request.POST.get('source', '').strip()
    first_seen_raw = request.POST.get('first_seen', '').strip()
    last_seen_raw = request.POST.get('last_seen', '').strip()

    # minimal validation
    if not value or not indicator_type:
        return HttpResponseBadRequest("Indicator value and type are required.")

    # severity is stored as int (default 1)
    try:
        severity = int(severity_raw or "1")
    except ValueError:
        severity = 1

    # parse datetimes (HTML datetime-local comes like "2025-10-31T08:41")
    # we convert to aware datetimes in server timezone
    def parse_dt(dt_str):
        if not dt_str:
            return None
        try:
            # assume it's local but naive ->  make_aware
            naive = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
            return make_aware(naive, timezone.get_current_timezone())
        except Exception:
            return None

    first_seen = parse_dt(first_seen_raw) or timezone.now()
    last_seen = parse_dt(last_seen_raw) or timezone.now()

    # save to DB
    item = IntelItem.objects.create(
        value=value,
        indicator_type=indicator_type,
        severity=severity or 1,
        confidence=confidence or 0,
        source=source or "Manual",
        first_seen=first_seen or "",
        last_seen=last_seen or "",
        created_by=request.user,
    )

    # Audit
    write_audit(
        request=request,
        action="intel.add",
        message=f"Added intel {item.value}",
        target_type="intel", target_id=item.id, target_repr=item.value,
        extra={
            "indicator_type": item.indicator_type,
            "severity": item.severity,
            "confidence": item.confidence,
            "source": item.source,
        }
    )

    # respond
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "id": item.id,
            "value": item.value,
            "indicator_type": item.indicator_type,
            "severity": item.severity,
            "severity_label": severity_label(item.severity),
            "confidence": item.confidence or "",
            "source": item.source or "",
            "first_seen": item.first_seen.strftime("%Y-%m-%d %H:%M") if item.first_seen else "",
            "last_seen": item.last_seen.strftime("%Y-%m-%d %H:%M") if item.last_seen else "",
        })
    else:
        # non-AJAX fallback (rare for you)
        return HttpResponseBadRequest("Only AJAX supported for now.")


@login_required
def intel_detail_json(request, pk):
    """
    Optional: return JSON for one intel item.
    Useful later for a 'view details' modal.
    """
    try:
        item = IntelItem.objects.get(pk=pk)
    except IntelItem.DoesNotExist:
        return HttpResponseBadRequest("Not found")

    return JsonResponse({
        "id": item.id,
        "value": item.value,
        "indicator_type": item.indicator_type,
        "severity": item.severity,
        "severity_label": severity_label(item.severity),
        "confidence": item.confidence or "",
        "source": item.source or "",
        "first_seen": item.first_seen.strftime("%Y-%m-%d %H:%M") if item.first_seen else "",
        "last_seen": item.last_seen.strftime("%Y-%m-%d %H:%M") if item.last_seen else "",
        "created_by": item.created_by.username if item.created_by else "—",
        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(item, "created_at") and item.created_at else "",
    })

@login_required
@require_POST
def fetch_intel_sources(request):
    """
    Pull intel from external providers, save new records, return a JSON summary.
    Returns:
      200 {ok: true, inserted: N, per_source: {...}}
      500 {ok: false, error: "..."}
    """
    try:
        # 1) Pull from all sources (each returns list[dict])
        abuse = fetch_from_abuseipdb() or []
        vt    = fetch_from_virustotal() or []
        otx   = fetch_from_otx() or []

        combined = abuse + vt + otx

        # 2) De-duplicate by (value, source)
        seen = set()
        unique = []
        for item in combined:
            key = (item.get("value"), item.get("source"))
            if not key[0] or not key[1]:
                continue
            if key not in seen:
                seen.add(key)
                unique.append(item)

        # 3) Insert if not present
        actually_added = []
        per_source_counter = Counter([i.get("source") for i in unique if i.get("source")])

        with transaction.atomic():
            for entry in unique:
                value = entry.get("value")
                source = entry.get("source")
                if not value or not source:
                    continue

                # timestamps default
                first_seen = entry.get("first_seen") or timezone.now()
                last_seen  = entry.get("last_seen")  or first_seen

                obj, created = IntelItem.objects.get_or_create(
                    value=value,
                    source=source,
                    defaults={
                        "indicator_type": entry.get("indicator_type", ""),
                        "severity":      entry.get("severity", 1),
                        "confidence":    entry.get("confidence", 0),
                        "first_seen":    first_seen,
                        "last_seen":     last_seen,
                        "created_by":    request.user,
                    },
                )
                if created:
                    actually_added.append(obj)

        added = len(actually_added)
        per_source = dict(per_source_counter)

        # 4) Audit (safe if you use it)
        try:
            write_audit(
                request=request,
                action="intel.fetch",
                message=f"Fetched intel from sources (added {added})",
                target_type="intel",
                extra={"added": added, "per_source": per_source},
            )
        except Exception:
            logger.debug("write_audit unavailable", exc_info=True)

        return JsonResponse(
            {"ok": True, "inserted": added, "per_source": per_source},
            status=200,
        )

    except Exception as e:
        logger.exception("Intel fetch failed")
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

def fetch_from_abuseipdb():
    """
    Returns a list of dicts like:
    {
      "value": "1.2.3.4",
      "indicator_type": "ip",
      "severity": 3,
      "confidence": "High",
      "source": "AbuseIPDB",
      "first_seen": "...",
      "last_seen": "...",
    }
    """
    api_key = os.getenv("ABUSEIPDB_API_KEY")
    if not api_key:
        return []

    # Example: fetch most-recently reported IPs.
    # AbuseIPDB "Blacklisted IPs" export /v2/blacklist is a common one.
    url = "https://api.abuseipdb.com/api/v2/blacklist"

    try:
        resp = requests.get(
            url,
            headers={
                "Key": api_key,
                "Accept": "application/json",
            },
                params={
                "limit": 10,  # limit how much we ingest per click
                "confidenceMinimum": 75,
            },
            timeout=20,
        )
    except requests.RequestException:
        return []

    if resp.status_code != 200:
        return []

    data = resp.json() or {}
    items = []

    # AbuseIPDB returns a list of {ipAddress, abuseConfidenceScore, lastReportedAt, ...}
    for entry in data.get("data", []):
        ip_addr = entry.get("ipAddress")
        conf_raw = entry.get("abuseConfidenceScore", 0)
        last_seen = entry.get("lastReportedAt", "")

        # Map confidence -> severity bucket
        # you can tune this however you want
        if conf_raw >= 90:
            sev = 4
            sev_conf_label = "High"
        elif conf_raw >= 70:
            sev = 3
            sev_conf_label = "High"
        elif conf_raw >= 40:
            sev = 2
            sev_conf_label = "Medium"
        else:
            sev = 1
            sev_conf_label = "Low"

        items.append({
            "value": ip_addr,
            "indicator_type": "ip",
            "severity": sev,
            "confidence": int(conf_raw),
            "source": "AbuseIPDB",
            "first_seen": "",         # AbuseIPDB doesn't always expose "first seen" here
            "last_seen": last_seen,
        })

    return items

def fetch_from_virustotal():
    """
    Demo: pretend we care about these IPs and ask VT for reputation.
    In reality, you'd drive this with your own IOC queue or VT hunting rules.
    """
    api_key = os.getenv("VT_API_KEY")
    if not api_key:
        return []

    suspicious_ips = [
        "45.76.123.22",
        "91.210.107.5",
    ]

    results = []
    for ip in suspicious_ips:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        resp = requests.get(
            url,
            headers={"x-apikey": api_key}
        )

        if resp.status_code != 200:
            continue

        j = resp.json()
        data = j.get("data", {})
        attrs = data.get("attributes", {})

        # We'll guess severity from number of malicious detections
        repscore = attrs.get("last_analysis_stats", {}).get("malicious", 0)
        if repscore >= 10:
            sev = 4
        elif repscore >= 5:
            sev = 3
        elif repscore >= 2:
            sev = 2
        else:
            sev = 1

        # we can say confidence is "High" if multiple vendors flag it
        confidence_label = "High" if repscore >= 5 else "Medium" if repscore >= 2 else "Low"

        # VT may not give first_seen easily in this endpoint, so we leave blank or "N/A"
    results.append({
        "value": ip,
        "indicator_type": "ip",
        "severity": sev,
        "confidence": map_confidence_to_score(confidence_label),
        "source": "VirusTotal",
        "first_seen": "",  # VT didn't give us first_seen cleanly
        "last_seen": timezone.now().strftime("%Y-%m-%d %H:%M"),
    })

    return results

def fetch_from_otx():
    """
    Pull indicators from OTX.
    We'll just hit your subscribed 'pulses' and extract some IOCs.
    """
    api_key = os.getenv("OTX_API_KEY")
    if not api_key:
        return []

    url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
    resp = requests.get(
        url,
        headers={"X-OTX-API-KEY": api_key},
        params={"limit": 5}   # don't explode the UI
    )

    if resp.status_code != 200:
        return []

    data = resp.json()
    items = []
    for pulse in data.get("results", []):
        pulse_name = pulse.get("name", "OTX Pulse")
        indicators = pulse.get("indicators", [])

        for i in indicators:
            ind_val = i.get("indicator")
            ind_type = i.get("type")  # 'IPv4', 'domain', 'URL', 'FileHash-SHA256', etc
            first_seen = pulse.get("created", "")
            last_seen = pulse.get("modified", "")

            # map OTX type -> your indicator_type
            if "IP" in ind_type.upper():
                indicator_type = "ip"
            elif "DOMAIN" in ind_type.upper():
                indicator_type = "domain"
            elif "URL" in ind_type.upper():
                indicator_type = "url"
            elif "HASH" in ind_type.upper():
                indicator_type = "hash"
            else:
                indicator_type = ind_type.lower()

            # we don't get numeric scores from OTX easily, so let's call them "Moderate"
            items.append({
                "value": ind_val,
                "indicator_type": indicator_type,
                "severity": 2,
                "confidence": map_confidence_to_score(pulse.get("indicator_confidence", "Medium")),
                "source": f"OTX ({pulse_name})",
                "first_seen": first_seen,
                "last_seen": last_seen,
            })

    return items

@login_required
def saved_search_list(request):
    searches = SavedSearch.objects.filter(owner=request.user)
    return render(request, "intel_saved_searches/list.html", {"searches": searches})

@login_required
def saved_search_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        query = request.POST.get("query")

        SavedSearch.objects.create(owner=request.user, name=name, query=query,)
        return redirect("intel_saved_search_list")

    return render(request, "intel_saved_searches/create.html")
