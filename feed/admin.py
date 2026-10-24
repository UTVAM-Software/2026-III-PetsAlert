from django.contrib import admin

from .models import PetReport


@admin.register(PetReport)
class PetReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'species', 'last_seen_location', 'user', 'is_active', 'is_resolved', 'created_at')
    list_filter = ('status', 'species', 'is_active', 'is_resolved')
    search_fields = ('description', 'last_seen_location', 'name', 'user__email', 'user__nombre')
    readonly_fields = ('created_at', 'updated_at')
