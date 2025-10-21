from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

@method_decorator(login_required, name="dispatch")
class DashboardView(TemplateView):
	template_name = "dashboard.html"

@login_required
def tech_profile(request):
	# TODO: replace with a real form later
	return render(request, "tech_profile.html", {})
