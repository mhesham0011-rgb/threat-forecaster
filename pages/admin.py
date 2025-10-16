from django.contrib import admin

from .models import Technology, UserProfile, ThreatAlert

# Register your models here to make them visible in the admin panel.
admin.site.register(Technology)
admin.site.register(UserProfile)
admin.site.register(ThreatAlert)