from django.shortcuts import render

import os
# Create your views here.
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from core.models import CartOrder, CartOrderItems, MiniSubCategory, Product, Category, ProductReview, Color, Size, ProductVariation,Vendor
from userauths.models import Profile, User
import datetime
from useradmin.forms import AddProductForm, VariationForm
from django.contrib.auth.decorators import login_required
from useradmin.decorators import admin_required
from django.http import JsonResponse
from core.models import SubCategory, MiniSubCategory
import json
import uuid
from django.core.files.storage import FileSystemStorage

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

@admin_required
def products(request):
    all_products = Product.objects.all().order_by("-id")
    all_categories = Category.objects.all()
    
    context = {
        "all_products": all_products,
        "all_categories": all_categories,
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
def edit_product(request, pid):
    product = Product.objects.get(pid=pid)

    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.save()
            form.save_m2m()
            return redirect("useradmin:dashboard-products")
    else:
        form = AddProductForm(instance=product)
    context = {
        'form':form,
        'product':product,
    }
    return render(request, "useradmin/edit-products.html", context)
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
    reviews = ProductReview.objects.all()
    context = {
        'reviews':reviews,
    }
    return render(request, "useradmin/reviews.html", context)


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