from django.core.management.base import BaseCommand
from taxonomy.attack_sync import load_attack_from_file, sync_attack_from_json


class Command(BaseCommand):
    help = "Sync MITRE ATT&CK data into local database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to ATT&CK JSON file",
            required=True,
        )

    def handle(self, *args, **options):
        path = options["file"]
        data = load_attack_from_file(path)
        sync_attack_from_json(data)
        self.stdout.write(self.style.SUCCESS("ATT&CK data synced successfully."))
