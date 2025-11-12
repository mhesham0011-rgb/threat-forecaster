from django.urls import path

from .views import saved_search_list, saved_search_create
from . import views

app_name = "intel"

urlpatterns = [
    path("", views.IntelListView.as_view(), name="index"),
    path("add/", views.intel_create, name="add"),
    path("<int:pk>/json/", views.intel_detail_json, name="detail_json"),
    path("fetch/", views.fetch_intel_sources, name="fetch"),

    path("saved-searches/", saved_search_list, name="intel_saved_search_list"),
    path("saved-searches/new/", saved_search_create, name="intel_saved_search_create"),
]
