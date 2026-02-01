from ast import Add
from core.models import Product, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address
from django.db.models import Min, Max, Count
from django.contrib import messages
from django.utils import timezone

from .recent_views import RecentViews


def default(request):
    categories = Category.objects.annotate(
        product_count=Count('subcategories__mini_subcategories__products')
    ).all()
    vendors = Vendor.objects.all()
    new_products = Product.objects.all().order_by("-id")[:6]
    try:
        deals_products = Product.objects.filter(has_deal=True).order_by("-deal_end_date")[:4]
    except:
        deals_products = []
    min_max_price = Product.objects.aggregate(Min("price"), Max("price"))

    if request.user.is_authenticated:
        try:
            wishlist = wishlist_model.objects.filter(user=request.user)
        except:
            messages.warning(request, "You need to login before accessing your wishlist.")
            wishlist = 0
    else:
        wishlist = 0
    
    for deal in deals_products:
        if deal.deal_end_date:
            # Compare directly with now()
            if deal.deal_end_date < timezone.now():
                deal.has_deal = False
                deal.deal_end_date = None
                deal.save()

    
    
    try:
        address = Address.objects.get(user=request.user)
    except:
        address = None

    return {
        'categories':categories,
        'wishlist':wishlist,
        'address':address,
        'vendors':vendors,
        'min_max_price':min_max_price,
        'new_products':new_products,
        'deals_products':deals_products,
    }

def cart_context(request):
    cart_count = 0
    if 'cart_data_obj' in request.session:
        cart_data = request.session['cart_data_obj']
        cart_count = sum(item['qty'] for item in cart_data.values())
    
    return {
        'cart_items_count': cart_count,
        'cart_data': request.session.get('cart_data_obj', {})
    }


def recently_viewed_products(request):
    """Context processor to add recently viewed products to all templates"""
    return {
        'recently_viewed_products': RecentViews.get_recent_views(request)
    }
