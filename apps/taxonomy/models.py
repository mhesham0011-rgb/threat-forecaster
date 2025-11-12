from django.db import models

class TaxonomyTerm(models.Model):
	"""
	Generic taxonomy term used by the web UI.
	"""

	vocab = models.CharField(max_length=64)
	key = models.CharField(max_length=64)
	label = models.CharField(max_length=128)
	order = models.IntegerField(default=0)
	color = models.CharField(max_length=32, blank=True)
	enabled = models.BooleanField(default=True)

	class Meta:
		unique_together = ("vocab", "key")
		ordering = ("vocab", "order", "key")

	def __str__(self):
		return f"{self.vocab}:{self.key} -> {self.label}"

class Tactic(models.Model):
	"""
	MITRE ATT&CK Tactic (e.g., Initial Access, Execution).
	"""

	attack_id = models.CharField(max_length=32, unique=True)
	name = models.CharField(max_length=28)
	description = models.TextField(blank=True)
	order = models.PositiveIntegerField(default=0)

	def __str__(self):
		return f"{self.attack_id} - {self.name}"

class Technique(models.Model):
	"""
	MITRE ATT&CK Technique or Sub-Technique.
	"""

	attack_id = models.CharField(max_length=32, unique=True)
	name = models.CharField(max_length=256)
	description = models.TextField(blank=True)
	tactic = models.ForeignKey(Tactic, related_name="techniques", on_delete=models.PROTECT)
	mitre_url = models.URLField(blank=True)
	platforms = models.JSONField(default=list, blank=True)
	is_deprecated = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.attack_id} - {self.name}"

class TechniqueStat(models.Model):
	"""
	Aggregated 'live' stats per technique from CIT & your detections.
	"""

	technique = models.OneToOneField(Technique, related_name="stats", on_delete=models.CASCADE)
	sightings_7d = models.PositiveIntegerField(default=0)
	sightings_30d = models.PositiveIntegerField(default=0)
	last_seen = models.DateTimeField(null=True, blank=True)
	coverage_score = models.FloatField(default=0.0)
	last_coverage_sync = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"Stats for {self.technique.attack_id}"

class CTIEvent(models.Model):
	"""
	A normalized CTI 'event' or report reference mapped to techniques.
	(No exploit details; just high-level metadata.)
	"""

	external_id = models.CharField(max_length=128, unique=True)
	title = models.CharField(max_length=512)
	source = models.CharField(max_length=128)
	summary = models.TextField(blank=True)
	published_at = models.DateTimeField()
	url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	techniques = models.ManyToManyField(Technique, related_name="cti_events", through="TechniqueSighting")

	def __str__(self):
		return f"{self.source}:{self.external_id} - {self.title}"

class TechniqueSighting(models.Model):
	"""
	Join table linking CTIEvent to Techniques, with sighting timestamp.
	"""

	technique = models.ForeignKey(Technique, on_delete=models.CASCADE)
	cti_event = models.ForeignKey(CTIEvent, on_delete=models.CASCADE)
	seen_at = models.DateTimeField()

	class Meta:
		unique_together = ("technique", "cti_event")

class DetectionRule(models.Model):
	"""
	Your detection logic mapped to ATT&CK techniques.
	This is purely defensive: descriptive metadata about rules.
	"""

	technique = models.ForeignKey(Technique, related_name = "detection_rules", on_delete=models.CASCADE)
	name = models.CharField(max_length=256)
	source_system = models.CharField(max_length=128)
	rule_id = models.CharField(max_length=256, blank=True)
	description = models.TextField(blank=True)
	enabled = models.BooleanField(default=True)
	last_tested = models.DateTimeField(null=True, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.source_system} - {self.name} ({self.technique.attack_id})"
