from django.contrib import admin

# Register your models here.
from django.contrib import admin
from core.models import CartOrderItems, Product,Coupon, Category, Vendor, CartOrder, ProductImages, ProductReview, wishlist_model, Address, SubCategory, MiniSubCategory

class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_editable = ['title', 'price', 'featured', 'product_status']
    list_display = ['user', 'title', 'product_image', 'price', 'mini_subcategory', 'vendor', 'featured', 'product_status', 'pid']
    list_filter = [
        'mini_subcategory__subcategory__category',
        'mini_subcategory__subcategory',
        'mini_subcategory',
        'product_status',
        'featured'
    ]
    search_fields = ['title', 'mini_subcategory__title']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'cid', 'product_count', 'category_image']
    list_filter = ['title']
    search_fields = ['title', 'description']
    prepopulated_fields = {'cid': ['title']}

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'cid', 'product_count', 'category_image']
    list_filter = ['category', 'category__title']
    search_fields = ['title', 'category__title', 'description']
    prepopulated_fields = {'cid': ['title']}

class MiniSubCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'subcategory', 'get_category', 'cid', 'product_count', 'category_image']
    list_filter = ['subcategory__category', 'subcategory']
    search_fields = ['title', 'subcategory__title', 'description']
    prepopulated_fields = {'cid': ['title']}
    
    def get_category(self, obj):
        return obj.subcategory.category.title
    get_category.short_description = 'Category'
    get_category.admin_order_field = 'subcategory__category'
    

class VendorAdmin(admin.ModelAdmin):
    list_display = ['title', 'vendor_image']


class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ['paid_status', 'product_status']
    list_display = ['user',  'price', 'paid_status', 'order_date','product_status', 'sku']


class CartOrderItemsAdmin(admin.ModelAdmin):
    list_display = ['order','item', 'order_img','qty', 'price', 'total']


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review', 'rating']


class wishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date']


class AddressAdmin(admin.ModelAdmin):
    list_editable = ['address', 'status']
    list_display = ['user', 'address', 'status']


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(MiniSubCategory, MiniSubCategoryAdmin)

admin.site.register(Vendor, VendorAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItems, CartOrderItemsAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(wishlist_model, wishlistAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Coupon)

