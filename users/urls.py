from django.urls import path
from .views import signup, dashboard_view

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('dashboard/', dashboard_view, name='dashboard'),
]
