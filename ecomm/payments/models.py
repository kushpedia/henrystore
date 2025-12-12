from django.db import models

class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    order_id = models.CharField(max_length=100, blank=True, null=True)  # Add this field
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_id = models.CharField(max_length=100, unique=True)
    mpesa_code = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='Pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this field

    def __str__(self):
        return f"{self.mpesa_code or 'No Code'} - {self.amount} KES"