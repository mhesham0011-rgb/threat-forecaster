import requests
from django.core.management.base import BaseCommand
from pages.models import UserProfile, ThreatAlert  # Import the new ThreatAlert model


class Command(BaseCommand):
    help = 'Fetches threats and matches them to user profiles'
    CISA_URL = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting threat matching process...'))

        try:
            response = requests.get(self.CISA_URL)
            response.raise_for_status()
            data = response.json()
            vulnerabilities = data.get('vulnerabilities', [])
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Error fetching data: {e}'))
            return

        # Get all user profiles that have selected technologies
        all_profiles = UserProfile.objects.prefetch_related('technologies')

        # Clear old alerts before creating new ones (optional, but good practice)
        ThreatAlert.objects.all().delete()

        # Loop through each vulnerability
        for vuln in vulnerabilities:
            vuln_name = vuln.get('vulnerabilityName')
            vuln_product = vuln.get('product', '').lower()
            vuln_desc = vuln.get('shortDescription')

            # Loop through each user's profile
            for profile in all_profiles:
                # Loop through each technology the user has selected
                for tech in profile.technologies.all():
                    # THE CORE MATCHING LOGIC: Check if the tech name is in the vulnerability's product string
                    if tech.name.lower() in vuln_product:
                        # MATCH FOUND! Create a new ThreatAlert in the database.
                        # get_or_create prevents creating duplicate alerts.
                        ThreatAlert.objects.get_or_create(
                            user=profile.user,
                            vulnerability_name=vuln_name,
                            defaults={'description': vuln_desc}
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"MATCH FOUND for {profile.user.username}: {tech.name} in {vuln_name}"))
                        break  # Move to the next vulnerability once a match is found for this user

        self.stdout.write(self.style.SUCCESS('Threat matching process complete!'))