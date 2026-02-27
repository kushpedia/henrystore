from django.shortcuts import render, get_object_or_404,redirect
from django.urls import reverse
import os
# Create your views here.
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from core.models import (
	CartOrder,CartOrderItems, MiniSubCategory, Product,
	Category, ProductReview, Color, Size, ProductVariation,Vendor,
    ReturnLog, ReturnRequest
    )
from userauths.models import Profile, User
import datetime
from useradmin.forms import AddProductForm, VariationForm
from django.http import JsonResponse,HttpResponse
from core.models import SubCategory, MiniSubCategory
import json
import uuid
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Q, Sum
from datetime import datetime, timedelta, date, time

import datetime
from django.utils import timezone
from userauths.models import ContactUs

from django.views.decorators.csrf import csrf_exempt

import csv
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import user_passes_test
from core.utils.email_utils import ReturnEmailService
import calendar

from corporate.models import UniqueVisit



def admin_required(view_func):
    """Decorator to check if user is admin/staff"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

# unique visit tracking view 
def visitor_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # BASIC STATS (these are correct)
    unique_today = UniqueVisit.objects.filter(visit_date=today).values('ip_address').distinct().count()
    unique_week = UniqueVisit.objects.filter(visit_date__gte=week_ago).values('ip_address').distinct().count()
    unique_month = UniqueVisit.objects.filter(visit_date__gte=month_ago).values('ip_address').distinct().count()
    unique_all = UniqueVisit.objects.values('ip_address').distinct().count()
    
    # TOTAL VISITS (for comparison)
    visits_today = UniqueVisit.objects.filter(visit_date=today).count()
    visits_week = UniqueVisit.objects.filter(visit_date__gte=week_ago).count()
    visits_month = UniqueVisit.objects.filter(visit_date__gte=month_ago).count()
    visits_all = UniqueVisit.objects.count()
    
    # Daily breakdown for last 7 days (for the table)
    visits_by_day = UniqueVisit.objects.filter(
        visit_date__gte=week_ago
    ).values('visit_date').annotate(
        count=Count('id'),
        unique_count=Count('ip_address', distinct=True)
    ).order_by('visit_date')
    
    # Add authenticated/anonymous counts per day (UNIQUE counts)
    for day in visits_by_day:
        day['authenticated_unique'] = UniqueVisit.objects.filter(
            visit_date=day['visit_date'],
            user__isnull=False
        ).values('user').distinct().count()
        day['anonymous_unique'] = UniqueVisit.objects.filter(
            visit_date=day['visit_date'],
            user__isnull=True
        ).values('ip_address').distinct().count()
    
    # AUTHENTICATED VS ANONYMOUS (UNIQUE counts for the week)
    authenticated_week_unique = UniqueVisit.objects.filter(
        user__isnull=False, 
        visit_date__gte=week_ago
    ).values('user').distinct().count()
    
    anonymous_week_unique = UniqueVisit.objects.filter(
        user__isnull=True, 
        visit_date__gte=week_ago
    ).values('ip_address').distinct().count()
    
    # AUTHENTICATED VS ANONYMOUS (UNIQUE counts all time)
    auth_all_unique = UniqueVisit.objects.filter(
        user__isnull=False
    ).values('user').distinct().count()
    
    anon_all_unique = UniqueVisit.objects.filter(
        user__isnull=True
    ).values('ip_address').distinct().count()
    
    # Last 30 days data for line/bar charts
    dates_30 = [today - timedelta(days=i) for i in range(29, -1, -1)]
    last_30_dates = [d.strftime('%Y-%m-%d') for d in dates_30]
    
    daily_uniques = []
    daily_totals = []
    for d in dates_30:
        daily_uniques.append(UniqueVisit.objects.filter(visit_date=d).values('ip_address').distinct().count())
        daily_totals.append(UniqueVisit.objects.filter(visit_date=d).count())
    
    # Calculate additional stats
    avg_daily_unique = sum(daily_uniques) / len(daily_uniques) if daily_uniques else 0
    peak_day_visits = max(daily_totals) if daily_totals else 0
    peak_day_date = dates_30[daily_totals.index(peak_day_visits)].strftime('%b %d') if peak_day_visits > 0 else 'N/A'
    
    # FIXED: Return rate (percentage of visitors who returned this week)
    
    returning_ips_count = UniqueVisit.objects.filter(
        visit_date__gte=week_ago
    ).values('ip_address').annotate(
        visit_count=Count('id')
    ).filter(visit_count__gt=1).count()
    
    return_rate = (returning_ips_count / unique_week * 100) if unique_week > 0 else 0
    
    # FIXED: Visits per unique (ratio for the week)
    visits_per_unique = (visits_week / unique_week) if unique_week > 0 else 0
    
    # FIXED: Authentication ratio (using UNIQUE counts)
    auth_ratio = (auth_all_unique / unique_all * 100) if unique_all > 0 else 0
    
    # FIXED: Anonymous ratio
    anon_ratio = (anon_all_unique / unique_all * 100) if unique_all > 0 else 0
    
    context = {
        # Basic stats (keep as is)
        'unique_visitors_today': unique_today,
        'unique_visitors_this_week': unique_week,
        'unique_visitors_this_month': unique_month,
        'total_unique_all_time': unique_all,
        
        # ADD THESE NEW CONTEXT VARIABLES
        'visits_today': visits_today,
        'visits_this_week': visits_week,
        'visits_this_month': visits_month,
        'total_visits_all_time': visits_all,
        
        # Daily breakdown (updated with unique counts)
        'visits_by_day': visits_by_day,
        
        # Authenticated stats (now using UNIQUE counts)
        'authenticated_visits_unique': authenticated_week_unique,
        'anonymous_visits_unique': anonymous_week_unique,
        
        # All-time auth/anonymous (UNIQUE)
        'auth_all_unique': auth_all_unique,
        'anon_all_unique': anon_all_unique,
        
        # Chart data (keep as is)
        'last_30_dates': json.dumps(last_30_dates),
        'last_30_uniques': json.dumps(daily_uniques),
        'last_30_totals': json.dumps(daily_totals),
        
        # FIXED STATS
        'avg_daily_unique': round(avg_daily_unique, 1),
        'peak_day_visits': peak_day_visits,
        'peak_day_date': peak_day_date,
        'return_rate': round(return_rate, 1),           # Now a percentage
        'visits_per_unique': round(visits_per_unique, 1), # NEW: ratio
        'auth_ratio': round(auth_ratio, 1),             # Now correct (≤100%)
        'anon_ratio': round(anon_ratio, 1),             # NEW
    }
    return render(request, 'useradmin/visitor_dashboard.html', context)

@admin_required
def dashboard(request):
    revenue = CartOrder.objects.filter(paid_status=True).aggregate(price=Sum("price"))
    total_orders_count = CartOrder.objects.filter()
    all_products = Product.objects.all()
    all_categories = Category.objects.all()
    new_customers = User.objects.all().order_by("-id")[:6]
    latest_orders = CartOrder.objects.all().order_by("-date")[:5]

    this_month = datetime.datetime.now().month
    monthly_revenue = CartOrder.objects.filter(paid_status=True,order_date__month=this_month).aggregate(price=Sum("price"))

    
    context = {
        "monthly_revenue": monthly_revenue,
        "revenue": revenue,
        "all_products": all_products,
        "all_categories": all_categories,
        "new_customers": new_customers,
        "latest_orders": latest_orders,
        "total_orders_count": total_orders_count,
    }
    return render(request, "useradmin/dashboard.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def products(request):
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    # Base queryset
    all_products = Product.objects.all().order_by("-id")
    
    # Apply filters
    if status_filter != 'all':
        all_products = all_products.filter(product_status=status_filter)
    
    if search_query:
        all_products = all_products.filter(
            title__icontains=search_query
        ) | all_products.filter(
            description__icontains=search_query
        )
    
    if category_filter:
        all_products = all_products.filter(mini_subcategory__subcategory__category__id=category_filter)
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)  # Changed to 12 for better grid layout
    
    paginator = Paginator(all_products, per_page)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get categories for filter dropdown
    all_categories = Category.objects.all()
    
    # Get current parameters for pagination links
    current_params = request.GET.copy()
    if 'page' in current_params:
        del current_params['page']
    
    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "all_categories": all_categories,
        "status_filter": status_filter,
        "search_query": search_query,
        "category_filter": category_filter,
        "current_params": current_params.urlencode(),
        "total_products": all_products.count(),
        "showing_start": (page_obj.number - 1) * paginator.per_page + 1,
        "showing_end": min(page_obj.number * paginator.per_page, paginator.count),
        "total_count": paginator.count,
    }
    return render(request, "useradmin/products.html", context)


@admin_required
def add_product(request):
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            try:            
                vendor = Vendor.objects.get(user=request.user)
                new_form.vendor = vendor
            except Vendor.DoesNotExist:
                vendor = Vendor.objects.create(user=request.user, title=f"{request.user.username}'s Store")
                new_form.vendor = vendor
            
            # Check if mini_subcategory is selected
            if not new_form.mini_subcategory:
                form.add_error('mini_subcategory', 'Please select a category')
                return render(request, "useradmin/add-products.html", {'form': form})
            
            new_form.save()
            form.save_m2m()  # Save ManyToMany fields (colors, sizes)
            
            # Handle variations if enabled
            if new_form.has_variations and 'variations_data' in request.POST:
                try:
                    variations_data = json.loads(request.POST.get('variations_data', '[]'))
                    
                    for i, variation in enumerate(variations_data):
                        # Create ProductVariation instance
                        variation_instance = ProductVariation(
                            product=new_form,
                            color_id=variation.get('color'),
                            size_id=variation.get('size'),
                            price=variation.get('price') or None,
                            old_price=variation.get('old_price') or None,
                            stock_count=variation.get('stock_count', 0),
                        )
                        
                        # Handle variation image upload
                        image_key = f'variation_image_{i}'
                        if image_key in request.FILES:
                            variation_instance.image = request.FILES[image_key]
                        
                        variation_instance.save()
                        
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error creating variations: {e}")
                    # Don't fail the product creation if variations fail
            
            return redirect("useradmin:dashboard-products")
    else:
        form = AddProductForm()
    
    context = {
        'form': form,
        'colors': Color.objects.all().order_by('name'),
        'sizes': Size.objects.all().order_by('name'),
    }
    return render(request, "useradmin/add-products.html", context)



# AJAX view for getting available colors/sizes
@csrf_exempt
def get_variation_options(request):
    """Get colors and sizes for variation creation"""
    if request.method == 'GET':
        colors = list(Color.objects.all().values('id', 'name', 'hex_code'))
        sizes = list(Size.objects.all().values('id', 'name'))
        return JsonResponse({
            'colors': colors,
            'sizes': sizes,
            'success': True
        })
    return JsonResponse({'success': False}, status=400)

@admin_required
def dashboard_edit_products(request, pid):
    """Redirect to Django admin product change form"""
    product = get_object_or_404(Product, pid=pid)  # Using pid instead of id
    
    # Redirect to Django admin change form
    app_label = product._meta.app_label
    model_name = product._meta.model_name
    
    # Construct the admin URL
    admin_url = reverse(f'admin:{app_label}_{model_name}_change', args=[product.id])
    return redirect(admin_url)

@admin_required
def delete_product(request, pid):
    product = Product.objects.get(pid=pid)
    product.delete()
    return redirect("useradmin:dashboard-products")


@admin_required
def orders(request):
    # Get all orders ordered by date
    orders_list = CartOrder.objects.all().order_by("-date")
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders_list = orders_list.filter(
            Q(oid__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Order ID specific search
    order_id_search = request.GET.get('order_id', '')
    if order_id_search:
        orders_list = orders_list.filter(oid__icontains=order_id_search)
    
    # Status filtering
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter != 'Show all':
        if status_filter == 'processing':
            orders_list = orders_list.filter(product_status='processing')
        elif status_filter == 'shipped':
            orders_list = orders_list.filter(product_status='shipped')
        elif status_filter == 'delivered':
            orders_list = orders_list.filter(product_status='delivered')
    
    # Pagination
    items_per_page = request.GET.get('per_page', '20')
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [20, 30, 40]:
            items_per_page = 20
    except ValueError:
        items_per_page = 20
    
    paginator = Paginator(orders_list, items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    # ========== GRAPH DATA ==========
    
    # 1. Orders by Status (Pie Chart)
    status_counts = CartOrder.objects.values('product_status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in status_counts:
        status_labels.append(item['product_status'].title() if item['product_status'] else 'Unknown')
        status_data.append(item['count'])
    
    # 2. Orders by Payment Status (Pie Chart)
    payment_counts = CartOrder.objects.values('paid_status').annotate(count=Count('id'))
    payment_labels = []
    payment_data = []
    for item in payment_counts:
        payment_labels.append('Paid' if item['paid_status'] else 'Unpaid')
        payment_data.append(item['count'])
    
    # 3. Daily Orders for Last 7 Days (Line Chart)
    last_7_days = []
    dates_labels = []
    today = timezone.now().date()
    
    for i in range(6, -1, -1):
        current_date = today - timedelta(days=i)
        dates_labels.append(current_date.strftime('%a, %b %d'))
        
        # Create datetime objects for start and end of day
        day_start = datetime.datetime(current_date.year, current_date.month, current_date.day).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = datetime.datetime(current_date.year, current_date.month, current_date.day).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = CartOrder.objects.filter(date__range=[day_start, day_end]).count()
        last_7_days.append(count)
    
    # 4. Monthly Orders for Last 6 Months (Simplified Version)
    monthly_orders = []
    month_labels = []
    today = timezone.now()
    
    for i in range(5, -1, -1):
        # Get first day of the month, i months ago
        year = today.year
        month = today.month - i
        
        # Adjust year if needed
        while month <= 0:
            month += 12
            year -= 1
        
        # First day of the month at 00:00:00
        month_start = datetime.datetime(year, month, 1, 0, 0, 0)
        
        # Last day of the month at 23:59:59
        if month == 12:
            month_end = datetime.datetime(year + 1, 1, 1, 23, 59, 59) - timedelta(days=1)
        else:
            month_end = datetime.datetime(year, month + 1, 1, 23, 59, 59) - timedelta(days=1)
        
        month_name = month_start.strftime('%b %Y')
        month_labels.append(month_name)
        
        count = CartOrder.objects.filter(date__range=[month_start, month_end]).count()
        monthly_orders.append(count)
    
    # 5. Revenue by Status
    revenue_by_status = CartOrder.objects.values('product_status').annotate(
        total=Sum('price')
    ).order_by('-total')
    
    # 6. Top Customers by Order Count
    top_customers = CartOrder.objects.values('full_name', 'email').annotate(
        order_count=Count('id'),
        total_spent=Sum('price')
    ).order_by('-order_count')[:5]
    
    # 7. Overall Statistics
    total_orders = CartOrder.objects.count()
    total_revenue = CartOrder.objects.aggregate(Sum('price'))['price__sum'] or 0
    paid_orders = CartOrder.objects.filter(paid_status=True).count()
    unpaid_orders = CartOrder.objects.filter(paid_status=False).count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Revenue statistics
    paid_revenue = CartOrder.objects.filter(paid_status=True).aggregate(Sum('price'))['price__sum'] or 0
    unpaid_revenue = CartOrder.objects.filter(paid_status=False).aggregate(Sum('price'))['price__sum'] or 0
    # 8. Payment Status Counts for display
    paid_count = CartOrder.objects.filter(paid_status=True).count()
    unpaid_count = CartOrder.objects.filter(paid_status=False).count()
    
    # Convert to JSON for JavaScript
    context = {
        'orders': orders,
        'search_query': search_query,
        'order_id_search': order_id_search,
        'status_filter': status_filter,
        'items_per_page': items_per_page,
        
        # Graph data as JSON
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'payment_labels': json.dumps(payment_labels),
        'payment_data': json.dumps(payment_data),
        'daily_labels': json.dumps(dates_labels),
        'daily_data': json.dumps(last_7_days),
        'monthly_labels': json.dumps(month_labels),
        'monthly_data': json.dumps(monthly_orders),
        
        # Original data for tables
        'status_counts': status_counts,
        'payment_counts': payment_counts,
        'revenue_by_status': revenue_by_status,
        'top_customers': top_customers,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'avg_order_value': avg_order_value,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'paid_revenue': paid_revenue,
        'unpaid_revenue': unpaid_revenue,
        
    }
    return render(request, "useradmin/orders.html", context)



@admin_required
def order_detail(request, id):
    order = CartOrder.objects.get(id=id)
    order_items = CartOrderItems.objects.filter(order=order)
    context = {
        'order':order,
        'order_items':order_items
    }
    return render(request, "useradmin/order_detail.html", context)


@csrf_exempt
@admin_required
def change_order_status(request, oid):
    order = CartOrder.objects.get(oid=oid)
    if request.method == "POST":
        status = request.POST.get("status")
        messages.success(request, f"Order status changed to {status}")
        if status == "delivered":
            order.paid_status = True
        order.product_status = status
        order.save()
    
    return redirect("useradmin:order_detail", order.id)

@admin_required
def shop_page(request):
    products = Product.objects.filter(user=request.user)
    revenue = CartOrder.objects.filter(paid_status=True).aggregate(price=Sum("price"))
    total_sales = CartOrderItems.objects.filter(order__paid_status=True).aggregate(qty=Sum("qty"))

    context = {
        'products':products,
        'revenue':revenue,
        'total_sales':total_sales,
    }
    return render(request, "useradmin/shop_page.html", context)

@admin_required
def reviews(request):
    # Get filter parameters
    rating_filter = request.GET.get('rating', 'all')
    date_range = request.GET.get('date_range', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    reviews = ProductReview.objects.all().order_by("-date")
    
    # Apply filters
    if rating_filter != 'all':
        reviews = reviews.filter(rating=rating_filter)
    
    if date_range != 'all':
        now = timezone.now()
        if date_range == 'today':
            reviews = reviews.filter(date__date=now.date())
        elif date_range == 'week':
            week_start = now - timedelta(days=now.weekday())
            reviews = reviews.filter(date__gte=week_start)
        elif date_range == 'month':
            month_start = now.replace(day=1)
            reviews = reviews.filter(date__gte=month_start)
    
    if search_query:
        reviews = reviews.filter(
            review__icontains=search_query
        ) | reviews.filter(
            product__title__icontains=search_query
        ) | reviews.filter(
            user__username__icontains=search_query
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(reviews, 25)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Calculate stats
    total_reviews = ProductReview.objects.count()
    avg_rating = ProductReview.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    critical_reviews = ProductReview.objects.filter(rating__lte=2).count()
    today_reviews = ProductReview.objects.filter(date__date=timezone.now().date()).count()
    
    # Get current parameters for pagination
    current_params = request.GET.copy()
    if 'page' in current_params:
        del current_params['page']
    
    context = {
        "reviews": page_obj,
        "page_obj": page_obj,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "critical_reviews": critical_reviews,
        "today_reviews": today_reviews,
        "current_rating": rating_filter,
        "date_range": date_range,
        "search_query": search_query,
        "current_params": current_params.urlencode(),
    }
    return render(request, "useradmin/reviews.html", context)


@admin_required
def contact_messages(request):
    """Main contact messages view with filtering and pagination"""
    # Get filter parameters
    status_filter = request.GET.get('status', 'unread')
    date_range = request.GET.get('date_range', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    messages = ContactUs.objects.all().order_by("-created_at")
    
    # Apply filters
    if status_filter == 'unread':
        messages = messages.filter(read=False)
    elif status_filter == 'read':
        messages = messages.filter(read=True)
    elif status_filter == 'replied':
        messages = messages.filter(replied=True)
    
    if date_range != 'all':
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            messages = messages.filter(created_at__gte=start_date)
        elif date_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            messages = messages.filter(created_at__gte=start_date.replace(hour=0, minute=0, second=0, microsecond=0))
        elif date_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            messages = messages.filter(created_at__gte=start_date)
    
    if search_query:
        messages = messages.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(messages, 2)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Calculate stats
    total_messages = ContactUs.objects.count()
    unread_messages = ContactUs.objects.filter(read=False).count()
    
    # Today's messages
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_messages = ContactUs.objects.filter(created_at__gte=today_start).count()
    
    replied_messages = ContactUs.objects.filter(replied=True).count()
    
    # Get current parameters for pagination
    current_params = request.GET.copy()
    if 'page' in current_params:
        del current_params['page']
    
    context = {
        "messages": page_obj,
        "page_obj": page_obj,
        "total_messages": total_messages,
        "unread_messages": unread_messages,
        "today_messages": today_messages,
        "replied_messages": replied_messages,
        "status_filter": status_filter,
        "date_range": date_range,
        "search_query": search_query,
        "current_params": current_params.urlencode(),
        "showing_start": (page_obj.number - 1) * paginator.per_page + 1 if paginator.count > 0 else 0,
        "showing_end": min(page_obj.number * paginator.per_page, paginator.count) if paginator.count > 0 else 0,
        "total_count": paginator.count,
    }
    return render(request, "useradmin/contact_messages.html", context)

# API VIEWS
@csrf_exempt
@admin_required
def api_contact_detail(request, message_id):
    """Get detailed message information"""
    try:
        message = ContactUs.objects.get(id=message_id)
        return JsonResponse({
            'message': {
                'id': message.id,
                'full_name': message.full_name,
                'email': message.email,
                'phone': message.phone or '',
                'subject': message.subject,
                'message': message.message,
                'read': message.read,
                'replied': message.replied,
                'reply_message': message.reply_message or '',
                'replied_at': message.replied_at.isoformat() if message.replied_at else None,
                'created_at': message.created_at.isoformat(),
                'read_at': message.read_at.isoformat() if message.read_at else None,
            }
        })
    except ContactUs.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

@csrf_exempt
@admin_required
def api_mark_as_read(request, message_id):
    """Mark a message as read"""
    try:
        message = ContactUs.objects.get(id=message_id)
        if not message.read:
            message.read = True
            message.read_by = request.user
            message.read_at = timezone.now()
            message.save()
        return JsonResponse({'success': True, 'read': message.read})
    except ContactUs.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

@csrf_exempt
@admin_required
def api_mark_all_read(request):
    """Mark all unread messages as read"""
    if request.method == 'POST':
        unread_messages = ContactUs.objects.filter(read=False)
        count = unread_messages.count()
        
        for message in unread_messages:
            message.read = True
            message.read_by = request.user
            message.read_at = timezone.now()
            message.save()
        
        return JsonResponse({'success': True, 'count': count})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
@admin_required
def api_toggle_read(request, message_id):
    """Toggle read/unread status"""
    try:
        message = ContactUs.objects.get(id=message_id)
        message.read = not message.read
        if message.read:
            message.read_by = request.user
            message.read_at = timezone.now()
        else:
            message.read_by = None
            message.read_at = None
        message.save()
        return JsonResponse({'success': True, 'read': message.read})
    except ContactUs.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

@csrf_exempt
@admin_required
def api_send_reply(request, message_id):
    """Send reply to a message"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = ContactUs.objects.get(id=message_id)
            
            # Here you would implement email sending
            # For now, just mark as replied and save the reply
            message.replied = True
            message.replied_by = request.user
            message.replied_at = timezone.now()
            message.reply_message = data.get('message', '')
            message.save()
            
            # TODO: Implement actual email sending
            # send_mail(
            #     data.get('subject', 'Re: ' + message.subject),
            #     data.get('message', ''),
            #     'noreply@kstores.com',
            #     [message.email],
            #     fail_silently=False,
            # )
            
            return JsonResponse({'success': True})
        except ContactUs.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
@admin_required
def api_delete_message(request, message_id):
    """Delete a message"""
    if request.method == 'DELETE':
        try:
            message = ContactUs.objects.get(id=message_id)
            message.delete()
            return JsonResponse({'success': True})
        except ContactUs.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
@admin_required
def api_delete_all_read(request):
    """Delete all read messages"""
    if request.method == 'DELETE':
        read_messages = ContactUs.objects.filter(read=True)
        count = read_messages.count()
        read_messages.delete()
        return JsonResponse({'success': True, 'count': count})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@admin_required
def api_export_messages(request):
    """Export messages to CSV"""
    # Apply the same filters as the main view
    status_filter = request.GET.get('status', 'all')
    date_range = request.GET.get('date_range', 'all')
    search_query = request.GET.get('search', '')
    
    messages = ContactUs.objects.all().order_by("-created_at")
    
    if status_filter != 'all':
        if status_filter == 'unread':
            messages = messages.filter(read=False)
        elif status_filter == 'read':
            messages = messages.filter(read=True)
        elif status_filter == 'replied':
            messages = messages.filter(replied=True)
    
    if date_range != 'all':
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            messages = messages.filter(created_at__gte=start_date)
        elif date_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            messages = messages.filter(created_at__gte=start_date.replace(hour=0, minute=0, second=0, microsecond=0))
        elif date_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            messages = messages.filter(created_at__gte=start_date)
    
    if search_query:
        messages = messages.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contact_messages.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Subject', 'Message', 'Status', 'Read At', 'Replied', 'Replied At', 'Created At'])
    
    for msg in messages:
        status = 'Unread'
        if msg.replied:
            status = 'Replied'
        elif msg.read:
            status = 'Read'
        
        writer.writerow([
            msg.id,
            msg.full_name,
            msg.email,
            msg.phone or '',
            msg.subject,
            msg.message[:500],  # Limit message length
            status,
            msg.read_at.strftime('%Y-%m-%d %H:%M:%S') if msg.read_at else '',
            'Yes' if msg.replied else 'No',
            msg.replied_at.strftime('%Y-%m-%d %H:%M:%S') if msg.replied_at else '',
            msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@admin_required
def api_unread_count(request):
    """Get count of unread messages for sidebar badge"""
    count = ContactUs.objects.filter(read=False).count()
    return JsonResponse({'count': count})

#  row click functionality
@admin_required
def mark_and_view_message(request, message_id):
    """Mark message as read and redirect to view"""
    try:
        message = ContactUs.objects.get(id=message_id)
        if not message.read:
            message.read = True
            message.read_by = request.user
            message.read_at = timezone.now()
            message.save()
        
        # You can redirect to a detail page or back with anchor
        django_messages.success(request, f"Message from {message.full_name} marked as read.")
        return redirect(f'{request.META.get("HTTP_REFERER", "/useradmin/contact-messages/")}#message-{message_id}')
    except ContactUs.DoesNotExist:
        django_messages.error(request, "Message not found.")
        return redirect('useradmin:dashboard-contact-messages')



# admin return management views


@admin_required
def admin_return_list(request):
    """
    Admin view to list all return requests
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    returns = ReturnRequest.objects.select_related(
        'order', 'user', 'order_item'
    ).prefetch_related('logs').all()
    
    # Apply filters
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    if search_query:
        returns = returns.filter(
            Q(rma_number__icontains=search_query) |
            Q(order__oid__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(order_item__item__icontains=search_query)
        )
    
    # Order by most recent
    returns = returns.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': ReturnRequest.objects.count(),
        'pending': ReturnRequest.objects.filter(status='pending').count(),
        'approved': ReturnRequest.objects.filter(status='approved').count(),
        'received': ReturnRequest.objects.filter(status='received').count(),
        'completed': ReturnRequest.objects.filter(status='completed').count(),
        'total_refund': ReturnRequest.objects.filter(
            status='completed'
        ).aggregate(total=Sum('refund_amount'))['total'] or 0,
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'current_status': status_filter,
        'search_query': search_query,
        'status_choices': ReturnRequest.ReturnStatus.choices,
    }
    return render(request, 'useradmin/return_list.html', context)


@admin_required
def admin_return_detail(request, pk):
    """
    Admin view to manage individual return request
    """
    return_request = get_object_or_404(
        ReturnRequest.objects.select_related(
            'order', 'user', 'order_item', 'order_item__product_id'
        ).prefetch_related('logs__user'),
        pk=pk
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            with transaction.atomic():
                old_status = return_request.status
                
                if action == 'approve':
                    return_request.status = 'approved'
                    return_request.approved_by = request.user
                    return_request.approved_at = timezone.now()
                    return_request.admin_notes = notes or "Return approved"
                    
                elif action == 'reject':
                    return_request.status = 'rejected'
                    return_request.admin_notes = notes or "Return rejected"
                    
                elif action == 'receive':
                    return_request.status = 'received'
                    return_request.item_condition = request.POST.get('condition')
                    return_request.admin_notes = notes or "Item received"
                    
                elif action == 'complete':
                    return_request.status = 'completed'
                    return_request.completed_at = timezone.now()
                    return_request.admin_notes = notes or "Refund processed"
                    
                elif action == 'update_tracking':
                    return_request.tracking_number = request.POST.get('tracking_number')
                    return_request.shipping_carrier = request.POST.get('shipping_carrier')
                    return_request.shipped_date = timezone.now()
                    return_request.status = 'approved'  # Ensure status is approved
                    
                return_request.save()
                
                # Create log entry
                ReturnLog.objects.create(
                    return_request=return_request,
                    user=request.user,
                    action=action.upper(),
                    from_status=old_status,
                    to_status=return_request.status,
                    notes=notes or f"Admin {action} action performed"
                )
                # SEND EMAILS BASED ON ACTION
                if action == 'approve':
                    ReturnEmailService.send_return_approved(return_request)
                elif action == 'reject':
                    ReturnEmailService.send_return_rejected(return_request)
                elif action == 'receive':
                    ReturnEmailService.send_return_received(return_request)
                elif action == 'complete':
                    ReturnEmailService.send_return_completed(return_request)
                    
                messages.success(request, f"Return {action} successfully!")
                
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('useradmin:admin-return-detail', pk=return_request.pk)
    
    context = {
        'return': return_request,
        'logs': return_request.logs.all().order_by('-created_at'),
        'condition_choices': ReturnRequest.CONDITION_CHOICES,
    }
    return render(request, 'useradmin/return_detail.html', context)



# update admin profile settings
@admin_required
def settings(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        image = request.FILES.get("image")
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        bio = request.POST.get("bio")
        address = request.POST.get("address")
        country = request.POST.get("country")
        print("image ===========", image)
        
        if image != None:
            profile.image = image
        profile.full_name = full_name
        profile.phone = phone
        profile.bio = bio
        profile.address = address
        profile.country = country

        profile.save()
        messages.success(request, "Profile Updated Successfully")
        return redirect("useradmin:settings")
    
    context = {
        'profile':profile,
    }
    return render(request, "useradmin/settings.html", context)


# change password
@login_required
@admin_required
def change_password(request):
    user = request.user

    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_new_password = request.POST.get("confirm_new_password")

        if confirm_new_password != new_password:
            messages.warning(request, "Confirm Password and New Password Does Not Match")
            return redirect("useradmin:change_password")
        
        if check_password(old_password, user.password):
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password Changed Successfully")
            return redirect("useradmin:change_password")
        else:
            messages.warning(request, "Old password is not correct")
            return redirect("useradmin:change_password")
    
    return render(request, "useradmin/change_password.html")



def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id)
    data = {sub.id: sub.title for sub in subcategories}
    return JsonResponse(data)

def get_mini_subcategories(request):
    subcategory_id = request.GET.get('subcategory_id')
    mini_subcategories = MiniSubCategory.objects.filter(subcategory_id=subcategory_id)
    data = {mini.id: mini.title for mini in mini_subcategories}
    return JsonResponse(data)