from django.contrib import admin
from .models import UniqueVisit

@admin.register(UniqueVisit)
class UniqueVisitAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'visit_date', 'user_agent_preview']
    list_filter = ['visit_date', 'user']
    search_fields = ['ip_address', 'user__email', 'user__username']
    date_hierarchy = 'visit_date'
    
    def user_agent_preview(self, obj):
        return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_preview.short_description = 'User Agent'