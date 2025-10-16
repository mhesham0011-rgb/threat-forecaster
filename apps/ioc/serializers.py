from rest_framework import serializers
from .models import IOC, Enrichment

class EnrichmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrichment
        fields = ('source','payload','score','created_at')

class IOCSerializer(serializers.ModelSerializer):
    enrichments = EnrichmentSerializer(many=True, read_only=True)
    class Meta:
        model = IOC
        fields = ('id','value','ioc_type','verdict','threat_score','tags',
                  'first_seen','last_seen','enrichments')
