from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import CaseListView, CaseCreateView, case_detail_json

app_name = "cases"

urlpatterns = [
    path("", login_required(CaseListView.as_view()), name="index"),
    path("add/", login_required(CaseCreateView.as_view()), name="add"),
    path("<int:pk>/json/", login_required(case_detail_json), name="detail_json"),
]
