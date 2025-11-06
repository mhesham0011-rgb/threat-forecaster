from django.urls import path
from . import views

app_name = "intel"

urlpatterns = [
    path("", views.IntelListView.as_view(), name="index"),
    path("add/", views.intel_create, name="add"),
    path("<int:pk>/json/", views.intel_detail_json, name="detail_json"),
    path("fetch/", views.fetch_intel_sources, name="fetch"),
]
