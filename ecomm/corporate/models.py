# models.py
from django.db import models
from django.conf import settings  # Import settings to get AUTH_USER_MODEL
from django.utils import timezone

class UniqueVisit(models.Model):
    # Use settings.AUTH_USER_MODEL instead of direct User model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    visit_date = models.DateField(default=timezone.now)
    
    class Meta:
        # Ensure only one visit per user/ip/date combination
        unique_together = ['user', 'ip_address', 'visit_date']
        ordering = ['-visit_date']
        
    def __str__(self):
        if self.user:
            return f"{self.user} - {self.visit_date}"
        return f"Anonymous - {self.visit_date}"