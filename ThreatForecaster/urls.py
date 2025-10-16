from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ioc.views import IOCViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r'ioc', IOCViewSet, basename='ioc')
urlpatterns = [
    # When the path is empty (the homepage), use the 'home' view
    path('admin/', admin.site.urls),

    # 1. The built-in Django 'Authentication' department
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # 2. Our custom 'Users' department
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/', include(router.urls)),
]
