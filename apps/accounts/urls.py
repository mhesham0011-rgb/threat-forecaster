from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .views import signup

app_name = "accounts"
urlpatterns = [
	path("profile/", login_required(TemplateView.as_view(template_name="account/profile.html")), name="profile"),
	path("signup/", signup, name="signup"),
]
