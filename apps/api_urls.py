from rest_framework.routers import DefaultRouter
from apps.ioc.views import IOCViewSet

router = DefaultRouter()

try:
	from apps.ioc.views import IOCViewSet
	if IOCViewSet:
		router.register(r'ioc', IOCViewSet, basename='ioc')
except Exception:
	IOCViewSet = None

urlpatterns = []
urlpatterns += router.urls
