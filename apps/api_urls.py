from django.urls import include, path
from rest_framework.routers import DefaultRouter

# import your viewsets
from apps.ioc.views import IOCViewSet	# adjust if your module is different

router = DefaultRouter()
router.register(r'ioc', IOCViewSet, basename='ioc')

urlpatterns = [
	path('', include(router.urls)),
	# If IOCViewSet has @action(detail=False, methods=['post'],name='lookup')
	# DRF will auto-create /ioc/lookup/ (no extra path needed here).
]
