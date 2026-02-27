# middleware.py

from django.utils.deprecation import MiddlewareMixin
from core.recent_views import RecentViews
from core.models import Product
from corporate.models import UniqueVisit
from django.utils import timezone

class RecentlyViewedMiddleware(MiddlewareMixin):
    """Middleware to track recently viewed products"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check if this is a product detail view and record the view
        """
        # Extract pid from URL parameters (matches your URL pattern)
        product_pid = view_kwargs.get('pid')
        
        if product_pid:
            try:
                product = Product.objects.get(pid=product_pid)
                RecentViews.add_product_view(request, product)
            except (Product.DoesNotExist, ValueError):
                # Product doesn't exist or invalid pid
                pass
        
        return None

class UniqueVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Only track if not in admin (optional)
        if not request.path.startswith('/admin/'):
            # Get or create a unique visit for today
            UniqueVisit.objects.get_or_create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                visit_date=timezone.now().date()
            )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')