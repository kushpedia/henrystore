from ast import Add
from core.models import Product, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address
from django.db.models import Min, Max
from django.contrib import messages
from django.utils import timezone

def default(request):
    categories = Category.objects.all()
    vendors = Vendor.objects.all()
    new_products = Product.objects.all().order_by("-id")[:4]
    deals_products = Product.objects.filter(has_deal=True).order_by("-deal_end_date")[:4]
    
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