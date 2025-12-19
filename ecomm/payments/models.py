# models.py - Enhanced Transaction model
from django.db import models

class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Expired', 'Expired'),
    ]
    
    ERROR_CATEGORIES = [
        ('user_error', 'User Error (e.g., wrong PIN, cancelled)'),
        ('balance_error', 'Balance Error'),
        ('limit_error', 'Limit Error'),
        ('system_error', 'System Error'),
        ('timeout_error', 'Timeout Error'),
    ]
    
    order_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_id = models.CharField(max_length=100, unique=True)
    mpesa_code = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='Pending')
    
    # Error tracking
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.TextField(blank=True, null=True)
    error_category = models.CharField(max_length=20, choices=ERROR_CATEGORIES, blank=True, null=True)
    user_action = models.CharField(max_length=50, blank=True, null=True)  # retry, contact_support, etc.
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.mpesa_code or 'No Code'} - {self.amount} KES - {self.status}"
    
    def mark_as_failed(self, result_code, result_desc, error_category, user_action):
        """Helper method to mark transaction as failed with details"""
        self.status = 'Failed'
        self.result_code = result_code
        self.result_desc = result_desc
        self.error_category = error_category
        self.user_action = user_action
        self.save()