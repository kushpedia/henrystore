from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
import stripe
from taggit.models import Tag
from core.models import CartOrderItems, Product, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address,Coupon,SubCategory,MiniSubCategory
from core.forms import ProductReviewForm
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required
from django.core import serializers
import calendar
from django.db.models.functions import ExtractMonth
from django.db.models import Count, Avg, Q
from userauths.models import ContactUs
from userauths.models import Profile

def index(request):
	products = Product.objects.filter(product_status="published", featured=True).order_by("-id")
	
	context = {'products': products}

	return render(request, 'core/index.html', context)


def product_list_view(request):
    products = Product.objects.filter(product_status="published").order_by("-id")
    # tags = Tag.objects.all().order_by("-id")[:6]

    context = {
        "products":products,
        # "tags":tags,
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

        context = {
            "category":category,
            "products":products,
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

        context = {
            "category":sub_category,
            "products":products,
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

        context = {
            "category":mini_category,
            "products":products,
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

    make_review = True 
    if request.user.is_authenticated:
        # address = Address.objects.get(status=True, user=request.user)
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False
    context = {
        "p": product,
        "review_form": review_form,
        "make_review": make_review,
        "p_images": product_images,

        "related_products":related_products,
        "average_rating": average_rating,
        "reviews": review,       

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




def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user 

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
        {
            'bool': True,
            'context': context,
            'average_reviews': average_reviews
        }
    )



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

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)

def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")

    # print("Categories Selected:", categories)
    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)


    if len(categories) > 0:
        products = products.filter(mini_subcategory__subcategory__category__id__in=categories)

    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors)

    
    data = render_to_string("core/async/product-list.html", {"products": products})
    return JsonResponse({"data": data})


def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'sku': request.GET['sku'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:

            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data

    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})



def cart_view(request):
    cart_total_amount = 0
    # print("cart data obj session:", request.session.get('cart_data_obj'))
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, "core/cart.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
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

@login_required
def checkout(request):
    cart_total_amount = 0
    total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])
    ############ Create Order ################
        order = CartOrder.objects.create(user=request.user,
                price=total_amount,)
        
    

        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

            ############ Create Order Items ################
            items = CartOrderItems.objects.create(
            order=order,
            invoice_no='INV-'+str(order.id),
            item=item['title'],
            image=item['image'],
            qty=item['qty'],
            price=item['price'],
            total=float(item['qty']) * float(item['price'])
        )



    host = request.get_host()
    paypal_dict={
        'business':settings.PAYPAL_RECEIVER_EMAIL,
        'amount':cart_total_amount,
        'item_name':'ORDER-ITEM-NO'+str(order.id),
        'invoice':"INVOICE-"+str(order.id),
        'currency_code':'USD',
        'notify_url': 'http://{}{}'.format(host,reverse('core:paypal-ipn')),
        'return_url': 'http://{}{}'.format(host,reverse('core:payment-completed')),
        'cancel_return': 'http://{}{}'.format(host,reverse('core:payment-failed')),
    }
    # Form to render the paypal button
    payment_button_form = PayPalPaymentsForm(initial=paypal_dict)

    # cart_total_amount = 0
    # if 'cart_data_obj' in request.session:
    #     for p_id, item in request.session['cart_data_obj'].items():
    #         cart_total_amount += int(item['qty']) * float(item['price'])
    
    try:
        active_address = Address.objects.filter(user=request.user, status=True).first()       
    except:
        messages.warning(request, "Only one active address allowed. Please set an address as default.")
    return render(request, "core/checkout.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount,'payment_button_form':payment_button_form,'active_address':active_address})
    

    return render(request, "core/checkout.html")


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
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,

    }
    return render(request, "core/new_checkout.html", context)

@csrf_exempt
def create_checkout_session(request, oid):
    order = CartOrder.objects.get(oid=oid)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email = order.email,
        payment_method_types=['card'],
        line_items = [
            {
                'price_data': {
                    'currency': 'USD',
                    'product_data': {
                        'name': order.full_name
                    },
                    'unit_amount': int(order.price * 100)
                },
                'quantity': 1
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse("core:payment-completed", args=[order.oid])) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse("core:payment-completed", args=[order.oid]))
    )

    order.paid_status = False
    order.stripe_payment_intent = checkout_session['id']
    order.save()

    # print("checkkout session", checkout_session)
    return JsonResponse({"sessionId": checkout_session.id})




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

            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])

            # Create ORder Object
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

            del request.session['full_name']
            del request.session['email']
            del request.session['mobile']
            del request.session['address']
            del request.session['city']
            del request.session['state']
            del request.session['country']

            # Getting total amount for The Cart
            for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])

                cart_order_products = CartOrderItems.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO-" + str(order.id), # INVOICE_NO-5,
                    item=item['title'],
                    image=item['image'],
                    qty=item['qty'],
                    price=item['price'],
                    total=float(item['qty']) * float(item['price'])
                )
        return redirect("core:new_checkout", order.oid)
    return redirect("core:new_checkout", order.oid)


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
    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
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




def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItems.objects.filter(order=order)

    
    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)


# wishlist view
@login_required
def wishlist_view(request):
    wishlist = wishlist_model.objects.filter(user=request.user)
    context = {
        "wishlist":wishlist
    }
    return render(request, "core/wishlist.html", context)



    # add to wishlist
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


# Other Pages 
def contact(request):
    return render(request, "core/contact.html")


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
        "message": "Message Sent Successfully"
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