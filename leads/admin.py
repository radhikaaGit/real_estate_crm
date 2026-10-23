from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "phone_number", "status", "lead_source", "assigned_to", "created_at")
    list_filter = ("status", "lead_source")
    search_fields = ("customer_name", "email", "phone_number")