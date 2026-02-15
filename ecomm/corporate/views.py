from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
import stripe
from taggit.models import Tag
from core.models import CartOrderItems, Product, Category,Color, Size, ProductVariation, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address,Coupon,SubCategory,MiniSubCategory
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
from django.db.models import Count, Avg, Q, Sum, Min, Max, F
from userauths.models import ContactUs
from userauths.models import Profile
import traceback
from django.db import models
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from django.utils import timezone
from decimal import Decimal
from django.template.loader import render_to_string
# Create your views here.
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





def affiliate_program(request):
    """Affiliate Program page - Learn about earning commissions"""
    categories = Category.objects.all()[:10]
    
    context = {
        'categories': categories,
        'page_name': 'Affiliate Program',
        'page_icon': '🤝',
        'page_description': 'Join our affiliate program and earn commissions by promoting KStores products.',
        'estimated_launch': 'Coming Q2 2026',
        'exception': 'Our affiliate program is currently under development. Soon you\'ll be able to earn commissions by sharing your favorite products!',
        'features': [
            {'icon': '💰', 'title': 'Competitive Commissions', 'description': 'Earn up to 15% on every sale'},
            {'icon': '📊', 'title': 'Real-time Tracking', 'description': 'Monitor your clicks, sales, and earnings'},
            {'icon': '🎯', 'title': 'Dedicated Support', 'description': 'Get help from our affiliate team'},
            {'icon': '🚀', 'title': 'Marketing Tools', 'description': 'Access banners, links, and promotional content'},
        ],
        'benefits': [
            '60-day cookie duration',
            'Monthly payouts via M-Pesa or Bank Transfer',
            'Exclusive affiliate-only promotions',
            'Dedicated affiliate manager',
            'Custom tracking links',
            'Bulk product feeds'
        ],
        'requirements': [
            'Website, blog, or social media presence',
            'Relevant audience in Kenya/East Africa',
            'Commitment to ethical marketing',
            '18 years or older'
        ],
        'cta_text': 'Join Waitlist',
        'cta_icon': 'fi-rs-user-add',
        'cta_url': '{% url "core:contact" %}?subject=Affiliate%20Program%20Inquiry',
    }
    return render(request, 'corporate/under_construction.html', context)

def our_suppliers(request):
    """Our Suppliers page - Vendor/supplier information"""
    categories = Category.objects.all()[:10]
    
    
    # Get active vendors to show as preview
    vendors = Vendor.objects.all()[:8]
    
    context = {
        'categories': categories,
        'page_name': 'Our Suppliers',
        'page_icon': '📦',
        'page_description': 'Meet the manufacturers who supply our products.',
        'estimated_launch': 'Coming Q2 2026',
        'exception': '🤝 We\'re building a directory of our trusted suppliers and partners. Soon you\'ll be able to learn more about where our products come from!',
        'features': [
            {'icon': '🏆', 'title': 'Quality Assured', 'description': 'Vetted and verified suppliers'},
            {'icon': '🌍', 'title': 'Local Sourcing', 'description': 'Supporting Kenyan businesses'},
            {'icon': '♻️', 'title': 'Sustainable Practices', 'description': 'Eco-friendly suppliers'},
            {'icon': '📱', 'title': 'Supplier Portal', 'description': 'Manage your products and orders'},
        ],
        'vendors': vendors,
        'supplier_categories': [            
            'Home Decor & Wall Art Artisans',
            'Blender & Mixer Manufacturers',
            'Laptop & Computer Suppliers',
            ' Beauty & Personal Care Product Makers',
            'Electronics Distributors'
        ],
        'cta_text': 'Become a Supplier',
        'cta_icon': 'fi-rs-store',
        'cta_url': '{% url "userauths:sign-up" %}?type=vendor',
    }
    return render(request, 'corporate/under_construction.html', context)

def accessibility(request):
    """Accessibility page - ADA compliance and inclusive shopping"""
    categories = Category.objects.all()[:10]
    
    
    context = {
        'categories': categories,
        'page_name': 'Accessibility',
        'page_icon': '♿',
        'page_description': 'Making KStores accessible to everyone.',
        'estimated_launch': 'Coming Q2 2026',
        'exception': 'We\'re committed to making KStores accessible to all users. Our accessibility features and compliance information will be available soon.',
        'features': [
            {'icon': '👁️', 'title': 'Screen Reader Compatible', 'description': 'WCAG 2.1 AA compliance'},
            {'icon': '⌨️', 'title': 'Keyboard Navigation', 'description': 'Full keyboard support'},
            {'icon': '🎨', 'title': 'High Contrast Mode', 'description': 'Better visibility options'},
            {'icon': '📝', 'title': 'Accessibility Statement', 'description': 'Our commitment to inclusion'},
        ],
        'accessibility_features': [
            'Alternative text for all images',
            'Proper heading structure',
            'ARIA labels for interactive elements',
            'Focus indicators for keyboard navigation',
            'Color contrast compliance',
            'Resizable text without loss of functionality',
            'Captions for video content',
            'Skip to main content links'
        ],
        'cta_text': 'Contact Accessibility Team',
        'cta_icon': 'fi-rs-headphones',
        'cta_url': '{% url "core:contact" %}?subject=Accessibility%20Inquiry',
    }
    return render(request, 'corporate/under_construction.html', context)



def promotions(request):
    """Promotions page - Deals, discounts, and special offers"""
    categories = Category.objects.all()[:10]
    
    
    # Get discounted products to show as preview
    discounted_products = Product.objects.all()[:8]
    
    # Sample upcoming promotions
    upcoming_promotions = [
        {'name': 'Black Friday Sale', 'month': 'November', 'discount': 'Up to 70%'},
        {'name': 'New Year Clearance', 'month': 'January', 'discount': 'Up to 50%'},
        {'name': 'Farmers Week', 'month': 'March', 'discount': '30% off agricultural products'},
        {'name': 'Back to School', 'month': 'August', 'discount': '25% off stationery'},
    ]
    
    context = {
        'categories': categories,
        'page_name': 'Promotions',
        'page_icon': '🎉',
        'page_description': 'Exclusive deals, seasonal sales, and special offers.',
        'estimated_launch': 'Coming Q1 2026',
        'exception': '🎁 Get ready for amazing deals! Our promotions hub is launching soon with exclusive discounts and special offers.',
        'features': [
            {'icon': '🏷️', 'title': 'Flash Sales', 'description': 'Limited-time deep discounts'},
            {'icon': '🎫', 'title': 'Coupon Codes', 'description': 'Extra savings on your purchases'},
            {'icon': '📅', 'title': 'Seasonal Events', 'description': 'Holiday and special occasion sales'},
            {'icon': '⭐', 'title': 'Member Exclusives', 'description': 'Special prices for registered users'},
        ],
        'discounted_products': discounted_products,
        'upcoming_promotions': upcoming_promotions,
        'cta_text': 'Get Notified',
        'cta_icon': 'fi-rs-bell',
        'cta_url': '{% url "core:contact" %}?subject=Promotions%20Notification',
    }
    return render(request, 'corporate/under_construction.html', context)