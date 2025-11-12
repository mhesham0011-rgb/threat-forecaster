from rest_framework import serializers
from .models import Tactic, Technique, TechniqueStat, CTIEvent, DetectionRule


class TechniqueStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechniqueStat
        fields = [
            "sightings_7d",
            "sightings_30d",
            "last_seen",
            "coverage_score",
            "last_coverage_sync",
        ]


class TechniqueListSerializer(serializers.ModelSerializer):
    stats = TechniqueStatSerializer(read_only=True)

    class Meta:
        model = Technique
        fields = [
            "id",
            "attack_id",
            "name",
            "tactic",
            "is_deprecated",
            "stats",
        ]


class TacticSerializer(serializers.ModelSerializer):
    techniques = TechniqueListSerializer(many=True, read_only=True)

    class Meta:
        model = Tactic
        fields = ["id", "attack_id", "name", "description", "order", "techniques"]


class DetectionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionRule
        fields = [
            "id",
            "name",
            "source_system",
            "rule_id",
            "description",
            "enabled",
            "last_tested",
        ]


class CTIEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CTIEvent
        fields = [
            "id",
            "external_id",
            "title",
            "source",
            "summary",
            "published_at",
            "url",
        ]


class TechniqueDetailSerializer(serializers.ModelSerializer):
    stats = TechniqueStatSerializer(read_only=True)
    detection_rules = DetectionRuleSerializer(many=True, read_only=True)
    cti_events = CTIEventSerializer(many=True, read_only=True)

    class Meta:
        model = Technique
        fields = [
            "id",
            "attack_id",
            "name",
            "description",
            "tactic",
            "mitre_url",
            "platforms",
            "is_deprecated",
            "stats",
            "detection_rules",
            "cti_events",
        ]
