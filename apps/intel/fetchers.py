# apps/intel/fetchers.py
import requests
from django.utils.timezone import make_aware
from datetime import datetime
from django.conf import settings
from .models import IntelItem

def parse_dt(val):
    # AbuseIPDB returns ISO8601 like "2025-10-30T14:22:15+00:00"
    # We convert to aware datetime Django can store
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = make_aware(dt)
        return dt
    except Exception:
        return None

def fetch_abuseipdb(ip_list, user):
    api_key = getattr(settings, "ABUSEIPDB_API_KEY", "")
    if not api_key:
        return [], "No AbuseIPDB API key configured"

    new_items = []

    for ip in ip_list:
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={
                "Key": api_key,
                "Accept": "application/json",
            },
            params={
                "ipAddress": ip,
                "maxAgeInDays": "90",
            },
            timeout=10,
        )

        if resp.status_code != 200:
            continue

        data = resp.json().get("data", {})

        score = data.get("abuseConfidenceScore")  # 0-100
        last = data.get("lastReportedAt")         # timestamp string

        # You decide what counts as "bad enough"
        if score and int(score) >= 50:
            item = IntelItem.objects.create(
                value=ip,
                indicator_type="IPv4",
                severity=3 if int(score) >= 75 else 2,  # map score → severity
                confidence="High" if int(score) >= 75 else "Medium",
                source="AbuseIPDB",
                first_seen=None,  # AbuseIPDB doesn't always give first seen
                last_seen=parse_dt(last),
                created_by=user,
            )
            new_items.append(item)

    return new_items, None
