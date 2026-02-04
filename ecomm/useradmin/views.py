from django.shortcuts import render, get_object_or_404,redirect
from django.urls import reverse
import os
# Create your views here.
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from core.models import CartOrder,CartOrderItems, MiniSubCategory, Product, Category, ProductReview, Color, Size, ProductVariation,Vendor
from userauths.models import Profile, User
import datetime
from useradmin.forms import AddProductForm, VariationForm
from useradmin.decorators import admin_required
from django.http import JsonResponse,HttpResponse
from core.models import SubCategory, MiniSubCategory
import json
import uuid
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.utils import timezone
from userauths.models import ContactUs

from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import csv
from django.contrib import messages as django_messages




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
    orders = CartOrder.objects.all().order_by("-date")
    context = {
        'orders':orders,
    }
    return render(request, "useradmin/orders.html", context)

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

# Add this view for row click functionality
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