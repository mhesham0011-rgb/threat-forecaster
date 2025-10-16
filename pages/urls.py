from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.tech_profile, name='tech_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]