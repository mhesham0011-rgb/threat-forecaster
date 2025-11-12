from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.urls import urlpatterns
from django.urls import path, include

from apps.accounts.views import custom_logout

urlpatterns = [
    path('admin/', admin.site.urls),

    # Registration
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/logout/", custom_logout, name="logout"),

    # UI sections per app
    path('', include(('apps.dashboard.urls'), namespace='dashboard')),
    path("ioc/", include(("apps.ioc.urls", 'ioc'), namespace="ioc")),
    path("cases/", include(("apps.cases.urls", "cases"), namespace="cases")),
    path("audit/", include(("apps.audit.urls", 'audit'), namespace="audit")),
    path("intel/", include(("apps.intel.urls", 'intel'), namespace="intel")),
    path("taxonomy/", include(("apps.taxonomy.urls", 'taxonomy'), namespace="taxonomy")),
]
