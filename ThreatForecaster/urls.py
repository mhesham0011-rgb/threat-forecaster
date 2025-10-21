from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import DashboardView, tech_profile

urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html"), name='home'),

    path('admin/', admin.site.urls),

    # Registration
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("django.contrib.auth.urls")), # login/logout

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),

    path('api/', include("apps.api_urls")),

    path('dashboard/', DashboardView.as_view(), name="dashboard"),

    path('tech-profile/', tech_profile, name="tech_profile"),

    # UI sections per app
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("ioc/", include("apps.ioc.urls", namespace="ioc")),
    path("cases/", include("apps.cases.urls", namespace="cases")),
    path("audit/", include("apps.audit.urls", namespace="audit")),
    path("intel/", include("apps.intel.urls", namespace="intel")),
    path("taxonomy", include("apps.taxonomy.urls", namespace="taxonomy")),
]
