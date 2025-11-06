from django.core.management.base import BaseCommand
from apps.taxonomy.models import TaxonomyTerm

SEED = [
    ("indicator_type","ip","IP Address",10,"danger",True),
    ("indicator_type","domain","Domain",20,"warning",True),
    ("indicator_type","url","URL",30,"primary",True),
    ("indicator_type","hash","Hash",40,"secondary",True),

    ("severity","5","Critical",50,"danger",True),
    ("severity","4","High",40,"warning",True),
    ("severity","3","Moderate",30,"info",True),
    ("severity","2","Low",20,"secondary",True),
    ("severity","1","Informational",10,"light",True),

    ("confidence","90","Very High",90,"success",True),
    ("confidence","80","High",80,"primary",True),
    ("confidence","60","Moderate",60,"info",True),
    ("confidence","40","Low",40,"secondary",True),

    ("case_status","open","Open",10,"danger",True),
    ("case_status","triage","Triage",20,"warning",True),
    ("case_status","closed","Closed",30,"success",True),

    ("intel_source","VirusTotal","VirusTotal",10,"secondary",True),
    ("intel_source","AbuseIPDB","AbuseIPDB",20,"secondary",True),
    ("intel_source","OTX","OTX",30,"secondary",True),
]

class Command(BaseCommand):
    help = "Seed default taxonomy terms"

    def handle(self, *args, **kwargs):
        for v,k,l,o,c,en in SEED:
            TaxonomyTerm.objects.get_or_create(
                vocab=v, key=k,
                defaults={"label":l, "order":o, "color":c, "enabled":en}
            )
        self.stdout.write(self.style.SUCCESS("Seeded taxonomy"))
