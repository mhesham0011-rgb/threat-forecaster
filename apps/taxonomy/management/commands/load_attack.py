import os
from django.core.management.base import BaseCommand, CommandError

from apps.taxonomy.loaders.load_attack import load_attack_from_file


class Command(BaseCommand):
    help = "Load/refresh MITRE ATT&CK techniques from a STIX 2.1 JSON file (e.g., enterprise-attack.json)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            required=True,
            help="Path to STIX JSON file (e.g., data/enterprise-attack.json)",
        )

    def handle(self, *args, **options):
        path = options["path"]

        if not os.path.isfile(path):
            raise CommandError(f"File not found: {path}")

        self.stdout.write(self.style.NOTICE(f"Loading ATT&CK techniques from: {path}"))
        created, updated = load_attack_from_file(path)
        self.stdout.write(self.style.SUCCESS(
            f"Done. Techniques created: {created}, updated: {updated}"
        ))
