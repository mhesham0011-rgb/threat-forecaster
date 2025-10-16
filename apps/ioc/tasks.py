from celery import shared_task
from .models import IOC, Enrichment
from .services.scoring import score_ioc
from apps.intel.providers import vt, otx, greynoise, shodan

@shared_task
def enrich_ioc(ioc_id:int):
    ioc = IOC.objects.get(id=ioc_id)
    results=[]
    for provider in (vt, otx, greynoise, shodan):
        try:
            data, src_score = provider.enrich(ioc.value, ioc.ioc_type)
            Enrichment.objects.create(ioc=ioc, source=provider.NAME, payload=data, score=src_score)
            results.append({'source': provider.NAME, 'score': src_score})
        except Exception:
            continue
    ioc.threat_score = score_ioc(results) if results else 0.0
    ioc.verdict = "malicious" if ioc.threat_score>=70 else "suspicious" if ioc.threat_score>=30 else "benign"
    ioc.save()
