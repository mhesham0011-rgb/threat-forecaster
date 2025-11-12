from datetime import timedelta
from django.utils.timezone import now

from .models import CTIEvent, Technique, TechniqueSighting, TechniqueStat


def fetch_cti_events_from_source():
    """
    Pseudocode: call TAXII/MISP/OpenCTI.
    Must return a list of items like:
    {
      "external_id": "...",
      "title": "...",
      "source": "MISP",
      "summary": "... (high level, no exploit code)",
      "published_at": datetime,
      "url": "https://...",
      "technique_ids": ["T1059", "T1566"]
    }
    """
    return []  # integrate later


def ingest_cti_events():
    events = fetch_cti_events_from_source()

    for item in events:
        event, created = CTIEvent.objects.update_or_create(
            external_id=item["external_id"],
            defaults={
                "title": item["title"],
                "source": item["source"],
                "summary": item.get("summary", ""),
                "published_at": item["published_at"],
                "url": item.get("url", ""),
            },
        )

        for tid in item.get("technique_ids", []):
            try:
                tech = Technique.objects.get(attack_id=tid)
            except Technique.DoesNotExist:
                continue

            TechniqueSighting.objects.get_or_create(
                technique=tech,
                cti_event=event,
                defaults={"seen_at": item["published_at"]},
            )

    # After ingest, recompute stats
    recompute_stats()


def recompute_stats():
    now_ts = now()
    from django.db.models import Count, Max

    for tech in Technique.objects.all():
        sightings = TechniqueSighting.objects.filter(technique=tech)
        last_7d = sightings.filter(seen_at__gte=now_ts - timedelta(days=7)).count()
        last_30d = sightings.filter(seen_at__gte=now_ts - timedelta(days=30)).count()
        last_seen = sightings.aggregate(last=Max("seen_at"))["last"]

        stat, _ = TechniqueStat.objects.get_or_create(technique=tech)
        stat.sightings_7d = last_7d
        stat.sightings_30d = last_30d
        stat.last_seen = last_seen
        stat.save()
