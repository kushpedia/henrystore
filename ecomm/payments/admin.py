from django.contrib import admin
from .models import Transaction
from django.utils import timezone

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'order_id', 
        'amount', 
        'phone_number', 
        'status',
        'mpesa_code', 
        'error_category',
        'timestamp'
    ]
    
    list_filter = [
        'status', 
        'error_category', 
        'timestamp',
        'user_action'
    ]
    
    search_fields = [
        'order_id', 
        'mpesa_code', 
        'phone_number', 
        'checkout_id',
        'result_desc'
    ]
    
    readonly_fields = [
        'timestamp', 
        'updated_at', 
        'checkout_id'
    ]
    
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'order_id', 
                'amount', 
                'phone_number', 
                'status'
            ]
        }),
        ('M-PESA Details', {
            'fields': [
                'checkout_id', 
                'mpesa_code'
            ]
        }),
        ('Error Information', {
            'fields': [
                'result_code', 
                'result_desc', 
                'error_category', 
                'user_action'
            ],
            'classes': ['collapse']  # Collapses this section by default
        }),
        ('Timestamps', {
            'fields': [
                'timestamp', 
                'updated_at', 
                'completed_at'
            ]
        }),
    ]
    
    actions = ['mark_as_processing', 'mark_as_success', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='Processing')
    mark_as_processing.short_description = "Mark selected transactions as Processing"
    
    def mark_as_success(self, request, queryset):
        
        queryset.update(status='Success', completed_at=timezone.now())
    mark_as_success.short_description = "Mark selected transactions as Success"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='Failed')
    mark_as_failed.short_description = "Mark selected transactions as Failed"
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly when editing existing objects"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ['checkout_id', 'timestamp']
        return self.readonly_fields