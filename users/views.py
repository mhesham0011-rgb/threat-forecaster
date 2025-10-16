# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')    # Redirect to login page after successfully sign-up
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})