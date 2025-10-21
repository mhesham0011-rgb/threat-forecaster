from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.contrib.auth import login

class SignupView(CreateView):
	form_class = UserCreationForm
	template_name = "registration/signup.html"
	success_url = reverse_lazy("login")	# send to login after signup

def signup(request):
	if request.method == "POST":
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect("dashboard")
	else:
		form = UserCreationForm()
	return render(request, "accounts/signup.html",{"form": form})
