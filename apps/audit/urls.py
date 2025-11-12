from django.urls import path

from .views import AuditListView, export_csv, saved_search_list, saved_search_create

app_name = "audit"

urlpatterns = [
    path("", AuditListView.as_view(), name="index"),
    path("list.json/", AuditListView.as_view(), name="list_json"),
    path("<int:pk>/json/", AuditListView.as_view(), name="detail_json"),
    path("export-csv", export_csv, name="export_csv"),

    path("saved-searches/", saved_search_list, name="audit_saved_search_list"),
    path("saved-searches/new/", saved_search_create, name="audit_saved_search_create"),
]
