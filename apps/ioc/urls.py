from django.urls import path
from .views import IOCListView, IOCCreateView, IOCIndex, saved_search_list, saved_search_create

app_name = "ioc"

urlpatterns = [
	path("", IOCListView.as_view(), name="index"),
	path("add/", IOCCreateView.as_view(), name="add"),
	path("ioc/", IOCIndex.as_view(), name="ioc-index"),

	path("saved-searches/", saved_search_list, name="ioc_saved_search_list"),
	path("saved-searches/new/", saved_search_create, name="ioc_saved_search_create"),
]
