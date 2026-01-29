# middleware.py
from django.utils.deprecation import MiddlewareMixin
from core.recent_views import RecentViews
from core.models import Product

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