from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import CaseListView, CaseCreateView, case_detail_json, saved_search_list, saved_search_create

from . import views

app_name = "cases"

urlpatterns = [
    path("", login_required(CaseListView.as_view()), name="index"),
    path("add/", login_required(CaseCreateView.as_view()), name="add"),
    path("<int:pk>/json/", login_required(case_detail_json), name="detail_json"),

    path("saved-searches/", saved_search_list, name="cases_saved_search_list"),
    path("saved-searches/new/", saved_search_create, name="cases_saved_search_create"),
    path("<int:pk>/", views.CaseDetailView.as_view(), name="detail"),
]
