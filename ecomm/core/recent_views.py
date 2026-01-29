# recent_views.py
from django.utils import timezone
from datetime import timedelta
from .models import Product, ProductView

class RecentViews:
    """Handle recent views for both authenticated and anonymous users"""
    
    MAX_ITEMS = 20
    SESSION_KEY = 'recently_viewed'
    EXPIRY_DAYS = 30
    
    @classmethod
    def add_product_view(cls, request, product):
        """Add a product to recently viewed for both user types"""
        
        # Check if product is in stock and published
        if not product.in_stock or not product.status or product.product_status != "published":
            return
        
        # For authenticated users
        if request.user.is_authenticated:
            cls._add_for_authenticated_user(request.user, product)
        # For anonymous users (session-based)
        else:
            cls._add_for_anonymous_user(request, product)
    
    @staticmethod
    def _add_for_authenticated_user(user, product):
        """Add view for authenticated user (database)"""
        # Using get_or_create to maintain original timestamp
        ProductView.objects.get_or_create(
            user=user,
            product=product,
            defaults={'viewed_on': timezone.now()}
        )
    
    @staticmethod
    def _add_for_anonymous_user(request, product):
        """Add view for anonymous user (session)"""
        if not hasattr(request, 'session'):
            return
        
        session_key = RecentViews.SESSION_KEY
        product_id = str(product.pid)  # Using pid (ShortUUID)
        
        # Initialize session data if not exists
        if session_key not in request.session:
            request.session[session_key] = {}
        
        # Get existing views
        viewed_products = request.session[session_key]
        
        # Check if product already exists (maintain original view time)
        if product_id not in viewed_products:
            # Add new product with current timestamp
            viewed_products[product_id] = timezone.now().isoformat()
        
        # Clean old entries
        RecentViews._clean_old_session_entries(viewed_products)
        
        # Limit to MAX_ITEMS
        if len(viewed_products) > RecentViews.MAX_ITEMS:
            sorted_items = sorted(
                viewed_products.items(),
                key=lambda x: x[1],
                reverse=True
            )[:RecentViews.MAX_ITEMS]
            viewed_products = dict(sorted_items)
        
        request.session[session_key] = viewed_products
        request.session.modified = True
    
    @staticmethod
    def _clean_old_session_entries(viewed_products):
        """Remove entries older than 30 days from session data"""
        cutoff_date = timezone.now() - timedelta(days=30)
        cutoff_str = cutoff_date.isoformat()
        
        to_remove = []
        for product_id, timestamp_str in viewed_products.items():
            if timestamp_str < cutoff_str:
                to_remove.append(product_id)
        
        for product_id in to_remove:
            del viewed_products[product_id]
    
    @classmethod
    def get_recent_views(cls, request):
        """Get recent views for the current user/session"""
        
        # For authenticated users
        if request.user.is_authenticated:
            views = ProductView.get_recent_views(request.user, cls.MAX_ITEMS)
            products = [view.product for view in views]
        
        # For anonymous users
        else:
            products = cls._get_for_anonymous_user(request)
        
        return products
    
    @staticmethod
    def _get_for_anonymous_user(request):
        """Get recent views from session for anonymous user"""
        if not hasattr(request, 'session'):
            return []
        
        session_key = RecentViews.SESSION_KEY
        if session_key not in request.session:
            return []
        
        viewed_products = request.session[session_key]
        
        # Clean old entries first
        RecentViews._clean_old_session_entries(viewed_products)
        request.session[session_key] = viewed_products
        
        # Get product IDs sorted by most recent
        sorted_product_ids = sorted(
            viewed_products.items(),
            key=lambda x: x[1],
            reverse=True
        )[:RecentViews.MAX_ITEMS]
        
        # Fetch products using pid (ShortUUID)
        product_pids = [pid for pid, _ in sorted_product_ids]
        
        products = Product.objects.filter(
            pid__in=product_pids,
            in_stock=True,
            status=True,
            product_status="published"
        )
        
        # Preserve order from session
        product_dict = {product.pid: product for product in products}
        ordered_products = []
        for pid in product_pids:
            if pid in product_dict:
                ordered_products.append(product_dict[pid])
        
        return ordered_products