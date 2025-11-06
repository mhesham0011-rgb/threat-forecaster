from django.urls import path
from . import views

app_name = "taxonomy"
urlpatterns = [
    path("", views.TaxonomyIndexView.as_view(), name="index"),
    path("list/", views.list_terms, name="list"),
    path("save/", views.save_term, name="save"),
    path("delete/", views.delete_term, name="delete"),
]
