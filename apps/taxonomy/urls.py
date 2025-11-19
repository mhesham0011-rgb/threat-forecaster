from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TacticViewSet, TechniqueViewSet, CTIEventViewSet, DetectionRuleViewSet, taxonomy_index, taxonomy_delete, taxonomy_list, taxonomy_save, live_summary
from . import views

app_name = "taxonomy"

router = DefaultRouter()
router.register(r"tactics", TacticViewSet, basename="tactic")
router.register(r"techniques", TechniqueViewSet, basename="technique")
router.register(r"cti-events", CTIEventViewSet, basename="cti-event")
router.register(r"detections", DetectionRuleViewSet, basename="detection-rule")

urlpatterns = [
    path("", taxonomy_index, name="index"),

    path("list/", taxonomy_list, name="list"),
    path("delete/", taxonomy_delete, name="delete"),
    path("save/", taxonomy_delete, name="save"),

    path("tactics/", views.TacticListView.as_view(), name="tactic-list"),
    path("techniques/", views.TechniqueListView.as_view(), name="technique-list"),
    path(
        "techniques/<str:attack_id>/",
        views.TechniqueDetailView.as_view(),
        name="technique-detail",
    ),
    path(
        "stats/techniques/",
        views.TechniqueStatsSummaryView.as_view(),
        name="technique-stats-summary",
    ),
    path("live/summary/", live_summary, name="live-summary"),
    path("terms/", views.taxonomy_terms_api, name="taxonomy-terms-api"),
]
