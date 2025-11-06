from django.contrib import admin
from .models import AuditEntry

@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "target_type", "message")
    search_fields = ("action", "message", "user__username")
    list_filter = ("action", "target_type", "timestamp")
