from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm

from apps.audit.utils import write_audit

class SignupView(CreateView):
	form_class = UserCreationForm
	template_name = "registration/signup.html"
	success_url = reverse_lazy("login")	# send to login after signup

def signup(request):
	if request.method == "POST":
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect("login")
	else:
		form = UserCreationForm()
	return render(request, "accounts/signup.html",{"form": form})

def custom_logout(request):
    # record audit safely
    try:
        write_audit(
            request=request,
            action="auth.logout",
            message="User logged out",
            target_type="auth",
        )
    except Exception:
        # don't block logout if audit fails
        pass

    # terminate the session and send to login page
    logout(request)
    return redirect("accounts:login")
