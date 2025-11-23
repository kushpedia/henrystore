from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from core.models import CartOrder, CartOrderItems, Product, Category, ProductReview
from userauths.models import Profile, User
import datetime
from useradmin.forms import AddProductForm

def dashboard(request):
    revenue = CartOrder.objects.aggregate(price=Sum("price"))
    total_orders_count = CartOrder.objects.all()
    all_products = Product.objects.all()
    all_categories = Category.objects.all()
    new_customers = User.objects.all().order_by("-id")[:6]
    latest_orders = CartOrder.objects.all()

    this_month = datetime.datetime.now().month
    monthly_revenue = CartOrder.objects.filter(order_date__month=this_month).aggregate(price=Sum("price"))

    
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

def products(request):
    all_products = Product.objects.all().order_by("-id")
    all_categories = Category.objects.all()
    
    context = {
        "all_products": all_products,
        "all_categories": all_categories,
    }
    return render(request, "useradmin/products.html", context)



def add_product(request):
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            form.save_m2m()
            return redirect("useradmin:dashboard-products")
    else:
        form = AddProductForm()
    context = {
        'form':form
    }
    return render(request, "useradmin/add-products.html", context)




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

def delete_product(request, pid):
    product = Product.objects.get(pid=pid)
    product.delete()
    return redirect("useradmin:dashboard-products")



def orders(request):
    orders = CartOrder.objects.all()
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
def change_order_status(request, oid):
    order = CartOrder.objects.get(oid=oid)
    if request.method == "POST":
        status = request.POST.get("status")
        messages.success(request, f"Order status changed to {status}")
        order.product_status = status
        order.save()
    
    return redirect("useradmin:order_detail", order.id)