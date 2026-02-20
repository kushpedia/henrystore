from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
import stripe
from taggit.models import Tag
from core.models import ( CartOrderItems, Product, Category,Color,
                Size, ProductVariation, Vendor, CartOrder, ProductImages, ProductReview, 
                wishlist_model, Address,Coupon,SubCategory,MiniSubCategory,ReturnRequest, ReturnLog)

from core.forms import ProductReviewForm, ReturnRequestForm
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required
from django.core import serializers
import calendar
from django.db import transaction
from django.db.models.functions import ExtractMonth
from django.db.models import Count, Avg, Q, Sum, Min, Max, F
from userauths.models import ContactUs
from userauths.models import Profile
import traceback
from django.db import models
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from django.utils import timezone
from decimal import Decimal
from django.template.loader import render_to_string
from .utils.email_utils import ReturnEmailService
# ================ CUSTOM ERROR HANDLERS ================

def custom_page_not_found(request, exception):
    """Custom 404 error handler"""
    categories = Category.objects.all()[:10]
    
    # Get recently viewed products from session
    recently_viewed = request.session.get('recently_viewed', [])
    recently_viewed_products = Product.objects.all()[:4] if recently_viewed else []
    
    context = {
        'categories': categories,
        'recently_viewed_products': recently_viewed_products,
        'exception': str(exception) if exception else 'The page you are looking for does not exist.',
        'debug': settings.DEBUG,
    }
    return render(request, '404.html', context, status=404)

def custom_server_error(request):
    """Custom 500 error handler"""
    categories = Category.objects.all()[:10]
    
    context = {
        'categories': categories,
        'exception': 'Something went wrong on our end. We are working to fix it!',
    }
    return render(request, '500.html', context, status=500)




def index(request):
    products = Product.objects.filter(product_status="published", featured=True).order_by("-id")
    top_sold_products = Product.objects.filter(
        product_status="published",
        cartorderitems__order__paid_status=True,
        cartorderitems__order__product_status="delivered"
    ).annotate(
        total_sold=Sum('cartorderitems__qty')
    ).filter(
        total_sold__gt=0  # Only include products that have actually been sold
    ).order_by('-total_sold')[:6]
    # print(top_sold_products)

    # Show top rated even with fewer reviews but high rating
    top_rated_products = Product.objects.filter(
        product_status="published"
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(
        review_count__gte=1,  # Minimum 1 reviews to qualify
        avg_rating__gte=2.0  # Only products with 4+ average rating
    ).order_by('-avg_rating', '-review_count')[:20]



    context = {
        'products': products,
        'top_sold_products': top_sold_products,
        'top_rated_products': top_rated_products,
    }

    return render(request, 'core/index.html', context)

# deals
def all_deals(request):
    # Get all active deals (not expired)
    deals_products = Product.objects.filter(
        has_deal=True,
        deal_end_date__gt=timezone.now()
    ).order_by("-deal_end_date")
    
    # Update any expired deals
    expired_deals = Product.objects.filter(
        has_deal=True,
        deal_end_date__lte=timezone.now()
    )
    expired_deals.update(has_deal=False, deal_end_date=None)
    
    # Pagination
    paginator = Paginator(deals_products, 6)  # Show 20 deals per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'deals_products': page_obj.object_list,
    }
    
    return render(request, 'core/deals.html', context)
def product_list_view(request):
    products = Product.objects.filter(product_status="published").order_by("-id")
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
        
    paginator = Paginator(products, per_page)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
        # Get current parameters
    current_params = request.GET.copy()
    if 'page' in current_params:
        del current_params['page']

    # Check if it's an AJAX request for infinite scroll
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            
            products_html = render_to_string('core/includes/product-cards.html', {
                'products': page_obj
            })
            return JsonResponse({
                'products_html': products_html,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
            })



    context = {
        "products": page_obj,  
        "page_obj": page_obj,
        "current_params": current_params.urlencode(),  
    }

    return render(request, 'core/product-list.html', context)

def category_list_view(request):
    categories = Category.objects.all()

    context = {
        "categories":categories
    }
    return render(request, 'core/category-list.html', context)


def category_product_list__view(request, cid):
    try:
        category = get_object_or_404(
            Category.objects.annotate(
                product_count=Count('subcategories__mini_subcategories__products')
            ),
            cid=cid
        ) 
        products = Product.objects.filter(
            product_status="published",
            mini_subcategory__subcategory__category=category
        ).order_by("-id")

        # Pagination
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 2)
        
        paginator = Paginator(products, per_page)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Get current parameters for pagination (excluding page)
        current_params = request.GET.copy()
        if 'page' in current_params:
            del current_params['page']
        
        # Check if it's an AJAX request for infinite scroll
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            products_html = render_to_string('core/includes/product-cards.html', {
                'products': page_obj
            })
            return JsonResponse({
                'products_html': products_html,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
            })

        context = {
            "category": category,
            "products": page_obj,
            "page_obj": page_obj,
            "current_params": current_params.urlencode(),
        }
        
    except:
        messages.warning(request, "Error Occurred. Please try again.")
        return redirect("core:index")
    
    return render(request, "core/category-product-list.html", context)
# items per sub category
def sub_category_product_list_view(request, cid):
    try:
        sub_category = get_object_or_404(
            SubCategory.objects.annotate(
                product_count=Count('mini_subcategories__products')
            ),
            cid=cid
        ) 
        
        products = Product.objects.filter(
            product_status="published",
            mini_subcategory__subcategory=sub_category  
        ).order_by("-id")

        # Pagination
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 2)
        
        paginator = Paginator(products, per_page)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Get current parameters for pagination (excluding page)
        current_params = request.GET.copy()
        if 'page' in current_params:
            del current_params['page']
        
        # Check if it's an AJAX request for infinite scroll
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            products_html = render_to_string('core/includes/product-cards.html', {
                'products': page_obj
            })
            return JsonResponse({
                'products_html': products_html,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
            })

        context = {
            "category": sub_category,
            "products": page_obj,
            "page_obj": page_obj,
            "current_params": current_params.urlencode(),
        }
        
    except:
        messages.warning(request, "Error Occurred. Please try again.")
        return redirect("core:index")
    
    return render(request, "core/sub-category-product-list.html", context)
# items per mini category
def mini_category_product_list_view(request, cid):
    try:
        mini_category = get_object_or_404(
            MiniSubCategory.objects.annotate(
                product_count=Count('products')
            ),
            cid=cid
        ) 
        
        products = Product.objects.filter(
            product_status="published",
            mini_subcategory=mini_category  
        ).order_by("-id")

        # Pagination
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 2)
        
        paginator = Paginator(products, per_page)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Get current parameters for pagination (excluding page)
        current_params = request.GET.copy()
        if 'page' in current_params:
            del current_params['page']
        
        # Check if it's an AJAX request for infinite scroll
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            products_html = render_to_string('core/includes/product-cards.html', {
                'products': page_obj
            })
            return JsonResponse({
                'products_html': products_html,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
            })

        context = {
            "category": mini_category,
            "products": page_obj,
            "page_obj": page_obj,
            "current_params": current_params.urlencode(),
        }
        
    except:
        messages.warning(request, "Error Occurred. Please try again.")
        return redirect("core:index")
    
    return render(request, "core/mini-category-product-list.html", context)


def vendor_list_view(request):
    vendors = Vendor.objects.all()
    context = {
        "vendors": vendors,
    }
    return render(request, "core/vendor-list.html", context)


def vendor_detail_view(request, vid):
    try:
        vendor = Vendor.objects.get(vid=vid)
        products = Product.objects.filter(vendor=vendor, product_status="published").order_by("-id")
    except:
        messages.warning(request, "Error Occurred. Please try again.")
        return redirect("core:index")
    context = {
        "vendor": vendor,
        "products": products,
    }
    return render(request, "core/vendor-detail.html", context)
def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    product_images = product.p_images.all()
    related_products = Product.objects.filter(
        mini_subcategory__subcategory=product.mini_subcategory.subcategory
    ).exclude(pid=product.pid).filter(product_status="published")
    review = ProductReview.objects.filter(product=product).order_by("-id")

    # Getting average review
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    # Product Review form
    review_form = ProductReviewForm()

    make_review = False
    has_ordered_product = False
    has_undelivered_product = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        # Check if user has ordered this product
        has_ordered_product = CartOrderItems.objects.filter(
            order__user=request.user,
            order__product_status="delivered",  # Order must be delivered
            original_title=product.title  # Assuming 'original_title' stores product title
        ).exists()

        # check the ordered product is not delivered yet
        has_undelivered_product = CartOrderItems.objects.filter(
            order__user=request.user,
            order__product_status__in=["processing", "shipped"],  # Un Delivered Orders
            original_title=product.title  
        ).exists()

        # Check if user has already reviewed this product
        has_reviewed = ProductReview.objects.filter(
            user=request.user, 
            product=product
        ).exists()

        # User can make review if they've ordered AND haven't reviewed yet
        make_review = has_ordered_product and not has_reviewed

    # ============ VARIATION LOGIC ============
    variations = None
    available_variations_dict = {}
    variation_colors = []
    variation_sizes = []
    
    if product.has_variations:
        # Get active variations
        variations = ProductVariation.objects.filter(
            product=product, 
            is_active=True
        ).select_related('color', 'size')
        
        # Create dictionary for available variations for JavaScript
        for variation in variations:
            color_id = str(variation.color.id) if variation.color else 'none'
            size_id = str(variation.size.id) if variation.size else 'none'
            key = f"{color_id}_{size_id}"
            
            available_variations_dict[key] = {
                'id': variation.id,
                'price': float(variation.get_final_price()),
                'old_price': float(variation.get_final_old_price()) if variation.get_final_old_price() else None,
                'stock_count': variation.stock_count,
                'in_stock': variation.is_in_stock(),
                'image': variation.variation_image(),
                'color_name': variation.color.name if variation.color else '',
                'size_name': variation.size.name if variation.size else '',
                'sku': variation.sku,
            }
        
        # Get unique colors and sizes from variations
        if variations.exists():
            # Get distinct colors
            color_ids = variations.exclude(color__isnull=True).values_list('color', flat=True).distinct()
            if color_ids:
                variation_colors = Color.objects.filter(id__in=color_ids)
            
            # Get distinct sizes
            size_ids = variations.exclude(size__isnull=True).values_list('size', flat=True).distinct()
            if size_ids:
                variation_sizes = Size.objects.filter(id__in=size_ids)
    
    # Convert available_variations_dict to JSON-safe format
    import json
    available_variations_json = json.dumps(available_variations_dict)
    # ============ END VARIATION LOGIC ============

    context = {
        "p": product,
        "review_form": review_form,
        "make_review": make_review,
        "p_images": product_images,
        "related_products": related_products,
        "average_rating": average_rating,
        "reviews": review,
        "has_undelivered_product": has_undelivered_product if request.user.is_authenticated else False,
        "has_reviewed": has_reviewed if request.user.is_authenticated else False,
        "has_ordered_product": has_ordered_product if request.user.is_authenticated else False,
        
        # Add variation data to context
        "variations": variations,
        "available_variations": available_variations_json,  # JSON for JavaScript
        "available_variations_dict": available_variations_dict,  # Dict for template
        "variation_colors": variation_colors,
        "variation_sizes": variation_sizes,
    }
    
    return render(request, "core/product-detail.html", context)

def tag_list(request, tag_slug=None):

    products = Product.objects.filter(product_status="published").order_by("-id")

    tag = None 
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products": products,
        "tag": tag
    }

    return render(request, "core/tag.html", context)




@csrf_exempt
def ajax_add_review(request, pid):
    
    
    try:
        if not request.user.is_authenticated:
            
            return JsonResponse({
                'bool': False, 
                'error': 'Please login to submit a review'
            }, status=401)
        
        try:
            product = Product.objects.get(pk=pid)
        except Product.DoesNotExist:
            return JsonResponse({
                'bool': False, 
                'error': 'Product not found'
            }, status=404)
        
        user = request.user
        
        # DEBUG: Check user's orders
        user_orders = CartOrderItems.objects.filter(
            order__user=user,
            order__product_status="delivered"
        )
        
        # Check if user has ordered this product AND it's delivered
        has_ordered = CartOrderItems.objects.filter(
            order__user=user,
            order__product_status="delivered"
        ).filter(
            models.Q(product_id=product) |  # Check product foreign key
            models.Q(original_title=product.title)  # Check original title
        ).exists()
        
        if not has_ordered:
            # Check if item field contains the product title
            has_ordered_via_item = CartOrderItems.objects.filter(
                order__user=user,
                order__product_status="delivered",
                item__contains=product.title  # Check if item contains product title
            ).exists()
            
            if not has_ordered_via_item:
                return JsonResponse({
                    'bool': False, 
                    'error': 'You can only review products you have purchased and received.'
                }, status=403)
        
        # Check if user has already reviewed this product
        existing_review = ProductReview.objects.filter(
            user=user,
            product=product
        ).exists()
        
        if existing_review:
            return JsonResponse({
                'bool': False, 
                'error': 'You have already reviewed this product.'
            }, status=400)

        # Get form data
        review_text = request.POST.get('review', '').strip()
        rating = request.POST.get('rating', '0').strip()
        
        if not review_text:
            return JsonResponse({
                'bool': False, 
                'error': 'Review text is required.'
            }, status=400)
        
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                return JsonResponse({
                    'bool': False, 
                    'error': 'Rating must be between 1 and 5.'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'bool': False, 
                'error': 'Invalid rating value.'
            }, status=400)

        # Create review
        review = ProductReview.objects.create(
            user=user,
            product=product,
            review=review_text,
            rating=rating_int,
        )

        context = {
            'user': user.username,
            'review': review_text,
            'rating': rating_int,
            'date': review.date.strftime("%d %B, %Y") if review.date else "Recently",
        }

        # Calculate new average rating
        average_reviews = ProductReview.objects.filter(product=product).aggregate(
            rating=Avg("rating")
        )
        
        avg_rating = float(average_reviews['rating'] or 0)
        
        return JsonResponse(
            {
                'bool': True,
                'context': context,
                'average_reviews': avg_rating,
                'message': 'Review submitted successfully!'
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        
        return JsonResponse({
            'bool': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def search_view(request):
    query = request.GET.get("q", "").strip()
    
    if not query:
        # Return empty results if no query
        context = {
            "products": Product.objects.none(),
            "query": "",
        }
        return render(request, "core/search.html", context)
    
    # Search across multiple fields and relationships
    products = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__name__icontains=query) |
        Q(vendor__title__icontains=query) |
        # Search through category hierarchy
        Q(mini_subcategory__title__icontains=query) |
        Q(mini_subcategory__subcategory__title__icontains=query) |
        Q(mini_subcategory__subcategory__category__title__icontains=query) |
        Q(specifications__icontains=query) |
        Q(type__icontains=query)
    ).filter(
        product_status="published"
    ).select_related(
        'vendor',
        'mini_subcategory__subcategory__category'
    ).prefetch_related(
        'tags'
    ).distinct().order_by("-date")

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 6)
    paginator = Paginator(products, per_page)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    current_params = request.GET.copy()
    if 'page' in current_params:
        del current_params['page']
    
    # Check if it's an AJAX request for infinite scroll
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        products_html = render_to_string('core/includes/product-cards.html', {
            'products': page_obj
        })
        return JsonResponse({
            'products_html': products_html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'query': query,
            'total_results': paginator.count,
        })

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "query": query,
        "current_params": current_params.urlencode(),
        "total_results": paginator.count,
    }
    return render(request, "core/search.html", context)

def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")

    # print("Categories Selected:", categories)
    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 2)

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)

    paginator = Paginator(products, per_page)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)


    if len(categories) > 0:
        products = products.filter(mini_subcategory__subcategory__category__id__in=categories)

    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors)

    
    data = render_to_string("core/async/product-list.html", {"products": products})
    return JsonResponse({"data": data})

# add to cart
@csrf_exempt
def add_to_cart(request):
    
    # Use request.POST since JavaScript sends POST
    if request.method == 'POST':
        data_source = request.POST
    else:
        # Fallback to GET for compatibility
        data_source = request.GET
    
    # Get all data from request
    cart_key = data_source.get('id', '').strip()
    pid = data_source.get('pid', '').strip()
    image = data_source.get('image', '').strip()
    qty = data_source.get('qty', '1').strip()
    title = data_source.get('title', '').strip()
    price = data_source.get('price', '0').strip()
    sku = data_source.get('sku', '').strip()
    
    # Get variation data
    variation_id = data_source.get('variation_id', '').strip()
    color = data_source.get('color', '').strip()
    size = data_source.get('size', '').strip()
    original_title = data_source.get('original_title', title).strip()
    
    # Validate required fields
    if not all([cart_key, pid, image, price]):
        return JsonResponse({
            'status': 'error',
            'message': 'Missing required fields',
            'totalcartitems': 0
        }, status=400)
    
    # Get the actual Product object
    try:
        product_obj = Product.objects.get(pid=pid)
        real_product_id = product_obj.id  # Store the actual model ID
    except Product.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Product not found',
            'totalcartitems': 0
        }, status=400)
    
    # Convert price to float for storage
    try:
        # Remove commas and convert to float
        price_float = float(str(price).replace(',', ''))
    except (ValueError, AttributeError):
        price_float = 0.0
    
    # Convert quantity to int
    try:
        qty_int = int(qty)
    except (ValueError, AttributeError):
        qty_int = 1
    
    # Build cart product dictionary
    cart_product = {
        'title': f"{original_title}",
        'qty': qty_int,
        'sku': sku,
        'price': price_float,  # Store as float
        'price_display': f"{price_float:,.0f}",  # Formatted for display
        'image': image,
        'pid': pid,
        'product_id': cart_key,
        'real_product_id': real_product_id,  # ADD THIS: Actual Product model ID
        'original_title': original_title,
        'variation_id': variation_id,
        'color': color,
        'size': size,
        'product_obj_title': product_obj.title,  # Store original product title too
    }
    
    # If color or size exists, add to title for display
    if color or size:
        variation_text = []
        if color and color.lower() != 'no-color':
            variation_text.append(f"Color: {color}")
        if size and size.lower() != 'no-size':
            variation_text.append(f"Size: {size}")
        if variation_text:
            cart_product['title'] = f"{original_title} ({', '.join(variation_text)})"
    
    # Initialize cart in session if not exists
    if 'cart_data_obj' not in request.session:
        request.session['cart_data_obj'] = {}
    
    cart_data = request.session['cart_data_obj']
    
    if cart_key in cart_data:
        # Same variation - update quantity
        cart_data[cart_key]['qty'] += qty_int  # Add to existing quantity
    else:
        # New variation - add new item
        cart_data[cart_key] = cart_product
    
    # Save session
    request.session.modified = True
    request.session['cart_data_obj'] = cart_data
    
    # Calculate total items count
    total_items = sum(item['qty'] for item in cart_data.values())
    
    return JsonResponse({
        "status": "success",
        "data": cart_data,
        'totalcartitems': total_items,
        'message': 'Product added to cart successfully'
    })


@login_required
def cart_view(request):
    cart_total_amount = 0
    
    if 'cart_data_obj' in request.session:
        cart_data = request.session['cart_data_obj']
        
        # Calculate total amount by iterating through cart items
        for product_id, item in cart_data.items():
            # Extract the price and quantity
            # Note: item['price'] might be a string with "Ksh " prefix or comma separators
            price_str = str(item['price'])
            
            # Clean the price string (remove currency symbol, commas, and whitespace)
            price_str = price_str.replace('Ksh', '').replace('$', '').replace(',', '').strip()
            
            try:
                # Convert to float then to Decimal for accurate calculation
                price = float(price_str)
                quantity = int(item['qty'])
                cart_total_amount += price * quantity
            except (ValueError, KeyError) as e:
                # Handle errors if price or quantity format is invalid
                print(f"Error processing cart item {product_id}: {e}")
                continue
        
        # Format the total amount (optional)
        cart_total_amount_formatted = "{:,.2f}".format(cart_total_amount)
        
        return render(request, "core/cart.html", {
            "cart_data": cart_data, 
            'totalcartitems': len(cart_data), 
            'cart_total_amount': cart_total_amount,
            'cart_total_amount_formatted': cart_total_amount_formatted
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")



def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})



def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})





@csrf_exempt
@login_required
def newCheckout(request, oid):
    order = CartOrder.objects.get(oid=oid)
    order_items = CartOrderItems.objects.filter(order=order)

    if request.method == "POST":
        code = request.POST.get("code")
        # print("code ========", code)
        coupon = Coupon.objects.filter(code=code, active=True).first()
        if coupon:
            if coupon in order.coupons.all():
                messages.warning(request, "Coupon already activated")
                return redirect("core:new_checkout", order.oid)
            else:
                discount = order.price * coupon.discount / 100 

                order.coupons.add(coupon)
                order.price -= discount
                order.saved += discount
                order.save()

                messages.success(request, "Coupon Activated")
                return redirect("core:new_checkout", order.oid)
        else:
            messages.warning(request, "Coupon Does Not Exist")

        

    context = {
        "order": order,
        "order_items": order_items,

    }
    return render(request, "core/new_checkout.html", context)


@csrf_exempt
@login_required
def save_checkout_info(request):
    cart_total_amount = 0
    total_amount = 0
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")

        request.session['full_name'] = full_name
        request.session['email'] = email
        request.session['mobile'] = mobile
        request.session['address'] = address
        request.session['city'] = city
        request.session['state'] = state
        request.session['country'] = country

        if 'cart_data_obj' in request.session:
            # Calculate total amount
            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])

            # Create Order Object
            order = CartOrder.objects.create(
                user=request.user,
                price=total_amount,
                full_name=full_name,
                email=email,
                phone=mobile,
                address=address,
                city=city,
                state=state,
                country=country,
            )

            # Clear session checkout data
            del request.session['full_name']
            del request.session['email']
            del request.session['mobile']
            del request.session['address']
            del request.session['city']
            del request.session['state']
            del request.session['country']

            # Create order items
            for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])
                
                # Get product using real_product_id
                product = None
                if 'real_product_id' in item:
                    try:
                        product = Product.objects.get(id=item['real_product_id'])
                    except Product.DoesNotExist:
                        print(f"Warning: Product with ID {item['real_product_id']} not found")
                
                # Fallback: Try to get product by pid if real_product_id fails
                if not product and 'pid' in item:
                    try:
                        product = Product.objects.get(pid=item['pid'])
                    except Product.DoesNotExist:
                        print(f"Warning: Product with PID {item['pid']} not found")
                
                # Get variation if exists
                variation = None
                if 'variation_id' in item and item['variation_id']:
                    try:
                        variation = ProductVariation.objects.get(id=item['variation_id'])
                    except ProductVariation.DoesNotExist:
                        variation = None
                
                # Create order item
                cart_order_products = CartOrderItems.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO-" + str(order.id),
                    item=item['title'],
                    product_id=product,  # Save the actual Product object
                    variation=variation,  # Save variation object
                    image=item['image'],
                    qty=item['qty'],
                    price=item['price'],
                    total=float(item['qty']) * float(item['price']),
                    color=item.get('color', ''),
                    size=item.get('size', ''),
                    original_title=item.get('original_title', item.get('product_obj_title', item['title']))
                )
                
        return redirect("core:new_checkout", order.oid)
    return redirect("core:index")

@login_required
def payment_completed_view(request,oid):
    order = CartOrder.objects.get(oid=oid)
    


    if order.paid_status == False:
        order.paid_status = True
        order.save()
    else:
        messages.warning(request, "Payment already completed for this order.")
        return redirect("core:index")

    

    # Clear the cart session after successful payment
    if 'cart_data_obj' in request.session:
        del request.session['cart_data_obj']
        messages.success(request, "Payment completed successfully")
        
    context = {
        "order": order,

    }
    return render(request, "core/payment-completed.html", context)


def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

# customer Dashboard
@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)
    returns = ReturnRequest.objects.select_related(
        'order', 'user', 'order_item'
    ).filter(user=request.user).order_by("-id")
    
    orders = CartOrder.objects.filter(user=request.user).annotate(
                month=ExtractMonth("order_date")
                ).values("month").annotate(
                    count=Count("id")
                ).values("month", "count").order_by("month")
    
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address_new = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address_new,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("error")
    user_profile = Profile.objects.get(user=request.user)

    context = {
        "user_profile":user_profile,
        "orders_list": orders_list,
        'addresses': address,
        "orders": orders,
        "month": month,
        "total_orders": total_orders,
        "returns": returns,
    }
    return render(request, 'core/dashboard.html', context)

# update default address
@login_required
def make_address_default(request):
    id = request.GET['id']
    user = request.user


    Address.objects.filter(user=user).update(status=False)
    Address.objects.filter(id=id, user=user).update(status=True)
    return JsonResponse({"boolean": True})



@csrf_exempt
def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItems.objects.filter(order=order)

    
    context = {
        "order_items": order_items,
        "order": order,
    }
    return render(request, 'core/order-detail.html', context)


# wishlist view
@csrf_exempt
@login_required
def wishlist_view(request):
    wishlist = wishlist_model.objects.filter(user=request.user)
    context = {
        "wishlist":wishlist
    }
    return render(request, "core/wishlist.html", context)



    # add to wishlist


@csrf_exempt
@login_required
def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)
    # print("product id isssssssssssss:" + product_id)

    context = {}

    wishlist_count = wishlist_model.objects.filter(product=product, user=request.user).count()
    # print(wishlist_count)

    if wishlist_count > 0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = wishlist_model.objects.create(
            user=request.user,
            product=product,
        )
        context = {
            "bool": True
        }

    return JsonResponse(context)  


# remove from wishlist
@csrf_exempt
def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = wishlist_model.objects.filter(user=request.user)
    wishlist_d = wishlist_model.objects.get(id=pid)
    delete_product = wishlist_d.delete()
    
    context = {
        "bool":True,
        "w":wishlist
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data':t,'w':wishlist_json})




# process returns

@login_required
def return_request_view(request, id):
    """
    Handle return request for a specific order item
    URL: /refund/<id>/
    """
    # Get the order item and verify it belongs to the logged-in user
    order_item = get_object_or_404(
        CartOrderItems, 
        id=id,
        order__user=request.user  # Ensures item belongs to user
    )
    cart_order_id = order_item.order.id
    # print("cart order id issssssssssssss:" + str(cart_order_id))
    
    # Check if item is eligible for return (7 days window)
    order_date = order_item.order.order_date
    days_since_order = (timezone.now() - order_date).days
    return_window = 7  # 7 days return window
    
    if days_since_order > return_window:
        messages.warning(
            request, 
            f"This item is no longer eligible for return. "
            f"Returns must be requested within {return_window} days of order."
        )
        return redirect('core:order-detail', cart_order_id)
    
    # Check if there's already a pending return for this item
    existing_return = ReturnRequest.objects.filter(
        order_item=order_item,
        status__in=['pending', 'approved', 'received']  # Active returns
    ).exists()
    
    if existing_return:
        messages.warning(
            request,
            "You already have an active return request for this item. "
            "Please wait for it to be processed."
        )
        return redirect('core:order-detail', cart_order_id)
    
    # Handle form submission
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, order_item=order_item)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the return request
                    return_request = form.save(commit=False)
                    return_request.order_item = order_item
                    return_request.order = order_item.order
                    return_request.user = request.user
                    
                    # Handle 'other' reason
                    reason = form.cleaned_data['reason']
                    if reason == 'other':
                        return_request.reason = form.cleaned_data['other_reason_text']
                    else:
                        # Get the display label for the reason
                        reason_dict = dict(form.REASON_CHOICES)
                        return_request.reason = reason_dict.get(reason, reason)
                    
                    # Calculate refund amount
                    return_request.refund_amount = order_item.price * form.cleaned_data['quantity']
                    
                    # Save the return request
                    return_request.save()
                    
                    # Create log entry
                    ReturnLog.objects.create(
                        return_request=return_request,
                        user=request.user,
                        action="RETURN_REQUESTED",
                        to_status=return_request.status,
                        notes=f"Return requested for {form.cleaned_data['quantity']} item(s)"
                    )
                    # SEND CONFIRMATION EMAIL
                    ReturnEmailService.send_return_confirmation(return_request)



                    messages.success(
                        request, 
                        f"Return request #{return_request.rma_number} has been submitted successfully!"
                    )
                    
                    # Redirect to return confirmation page
                    return redirect('core:return-confirmation', rma_number=return_request.rma_number)
                    
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReturnRequestForm(order_item=order_item)
    
    # Context for the template
    context = {
        'order_item': order_item,
        'form': form,
        'return_window': return_window,
        'days_since_order': days_since_order,
        'max_refund': order_item.price * order_item.qty,
    }
    
    return render(request, 'core/return-request.html', context)


@login_required
def return_confirmation_view(request, rma_number):
    """
    Show return request confirmation
    """
    return_request = get_object_or_404(
        ReturnRequest,
        rma_number=rma_number,
        user=request.user
    )
    
    context = {
        'return_request': return_request,
    }
    return render(request, 'core/return_confirmation.html', context)

# views.py - Add this new view

@login_required
def return_status_view(request, rma_number):
    """
    Track the status of a return request
    """
    return_request = get_object_or_404(
        ReturnRequest,
        rma_number=rma_number,
        user=request.user
    )
    
    # Get all logs for this return
    logs = return_request.logs.all().order_by('-created_at')
    
    # Define status timeline with icons and descriptions
    status_timeline = [
        {
            'status': 'pending',
            'label': 'Request Submitted',
            'icon': 'fi-rs-send',
            'description': 'Your return request has been submitted and is waiting for review.',
            'date': return_request.created_at,
            'completed': True
        },
        {
            'status': 'approved',
            'label': 'Return Approved',
            'icon': 'fi-rs-check',
            'description': 'Your return has been approved. Please ship the item back.',
            'date': return_request.approved_at,
            'completed': return_request.status in ['approved', 'received', 'completed']
        },
        {
            'status': 'received',
            'label': 'Item Received',
            'icon': 'fi-rs-package',
            'description': 'We have received your returned item and are inspecting it.',
            'date': None,  # Will be filled from logs
            'completed': return_request.status in ['received', 'completed']
        },
        {
            'status': 'completed',
            'label': 'Refund Processed',
            'icon': 'fi-rs-credit-card',
            'description': 'Your refund has been processed successfully.',
            'date': return_request.completed_at,
            'completed': return_request.status == 'completed'
        },
    ]
    
    # If rejected, show rejection reason
    if return_request.status == 'rejected':
        status_timeline = [
            {
                'status': 'pending',
                'label': 'Request Submitted',
                'icon': 'fi-rs-send',
                'date': return_request.created_at,
                'completed': True
            },
            {
                'status': 'rejected',
                'label': 'Return Rejected',
                'icon': 'fi-rs-times-circle',
                'description': return_request.admin_notes or 'Your return request was not approved.',
                'date': return_request.updated_at,
                'completed': True,
                'is_rejected': True
            },
        ]
    
    context = {
        'return': return_request,
        'logs': logs,
        'status_timeline': status_timeline,
    }
    return render(request, 'core/return_status.html', context)

# update tracking number
@login_required
def add_return_tracking(request, id):
    return_request = get_object_or_404(ReturnRequest, id=id, user=request.user)
    
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number')
        shipping_carrier = request.POST.get('shipping_carrier')
        
        if tracking_number and shipping_carrier:
            return_request.tracking_number = tracking_number
            return_request.shipping_carrier = shipping_carrier
            return_request.shipped_date = timezone.now()
            return_request.save()
            
            # Log the action
            ReturnLog.objects.create(
                return_request=return_request,
                user=request.user,
                action="TRACKING_ADDED",
                notes=f"Customer added tracking: {shipping_carrier} - {tracking_number}"
            )
            
            messages.success(request, "Tracking information added successfully!")
        else:
            messages.error(request, "Please provide both carrier and tracking number.")
    
    return redirect('core:dashboard')












# Other Pages 
def contact(request):
    return render(request, "core/contact.html")

@csrf_exempt
def ajax_contact_form(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    subject = request.GET['subject']
    message = request.GET['message']

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully, We will get back to you soon."
    }

    return JsonResponse({"data":data})


def about_us(request):
    return render(request, "core/about_us.html")


def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")



