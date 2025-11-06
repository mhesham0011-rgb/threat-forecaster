from django.urls import path
from .views import IOCListView, IOCCreateView

app_name = "ioc"

urlpatterns = [
	path("", IOCListView.as_view(), name="index"),
	path("add/", IOCCreateView.as_view(), name="add")
]
