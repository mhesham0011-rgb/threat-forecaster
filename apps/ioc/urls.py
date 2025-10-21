from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

app_name = "ioc"
urlpatterns = [
	path("", login_required(TemplateView.as_view(template_name="ioc/index.html")), name="index"),
]
