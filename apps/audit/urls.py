from django.urls import path
from .views import AuditListView, export_csv

app_name = "audit"

urlpatterns = [
    path("", AuditListView.as_view(), name="index"),
    path("list.json/", AuditListView.as_view(), name="list_json"),
    path("<int:pk>/json/", AuditListView.as_view(), name="detail_json"),
    path("export-csv", export_csv, name="export_csv"),
]
