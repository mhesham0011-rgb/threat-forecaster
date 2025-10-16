from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import IOC
from .serializers import IOCSerializer
from .tasks import enrich_ioc

class IOCViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = IOC.objects.all()
    serializer_class = IOCSerializer
    lookup_field = 'value'  # GET /api/ioc/{value}/

    @action(detail=False, methods=['post'])
    def lookup(self, request):
        value = request.data['value']
        ioc_type = request.data['ioc_type']
        ioc, _ = IOC.objects.get_or_create(value=value, defaults={'ioc_type': ioc_type})
        enrich_ioc.delay(ioc.id)
        return Response(IOCSerializer(ioc).data)
