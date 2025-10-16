from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Technology, UserProfile
from .models import ThreatAlert

@login_required
def tech_profile(request):
    # Make sure a user profile exists for the logged-in user
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Clear existing selections
        user_profile.technologies.clear()
        # Get the list of technology IDs that the user checked
        tech_ids = request.POST.getlist('technologies')
        for tech_id in tech_ids:
            technology = Technology.objects.get(id=tech_id)
            user_profile.technologies.add(technology)
        return redirect('home')     # Redirect to homepage after saving

    all_techs = Technology.objects.all()
    context = {
        'all_technologies': all_techs,
        'user_technologies': user_profile.technologies.all()
    }
    return render(request, 'tech_profile.html', context)
def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):
    # Fetch alerts that belong only to the current logged-in user
    alerts = ThreatAlert.objects.filter(user=request.user)
    context = {
        'alerts': alerts,
    }
    return render(request, 'dashboard.html', context)