from rest_framework import serializers
from .models import IOC

class IOCSerializer(serializers.ModelSerializer):
    class Meta:
        model = IOC
        fields = ('id','value','ioc_type','verdict','threat_score','tags',
                  'first_seen','last_seen','enrichments')
