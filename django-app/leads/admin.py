from django.contrib import admin

from .models import AuditLog, Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "status", "created_at")
    list_filter = ("status",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "message")
    readonly_fields = ("created_at", "message")
