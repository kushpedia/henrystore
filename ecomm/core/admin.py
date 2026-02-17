from django.contrib import admin

# Register your models here.
from django.contrib import admin
from core.models import ( CartOrderItems, Product,Coupon, Category,
						Vendor, CartOrder, ProductImages, ProductReview,
						wishlist_model, Address, SubCategory, MiniSubCategory,
						Color, Size, ProductVariation,ReturnRequest, ReturnLog)

admin.site.register(ReturnRequest)
admin.site.register(ReturnLog)



@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code', 'color_preview']
    list_filter = ['name']
    search_fields = ['name']
    list_per_page = 20

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 20

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'size', 'price', 'stock_count', 'is_active', 'sku']
    list_filter = ['is_active', 'color', 'size']
    search_fields = ['product__title', 'sku', 'color__name', 'size__name']
    list_editable = ['price', 'stock_count', 'is_active']
    list_per_page = 20
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter choices based on the product being edited"""
        if db_field.name == "color" or db_field.name == "size":
            # Try to get product ID from the URL or form
            if 'object_id' in request.resolver_match.kwargs:
                variation_id = request.resolver_match.kwargs.get('object_id')
                try:
                    variation = ProductVariation.objects.get(id=variation_id)
                    product = variation.product
                except ProductVariation.DoesNotExist:
                    pass
                else:
                    if db_field.name == "color":
                        kwargs["queryset"] = product.available_colors.all()
                    elif db_field.name == "size":
                        kwargs["queryset"] = product.available_sizes.all()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    max_num = 20  # Limit to prevent too many inlines
    fields = ['color', 'size', 'price', 'old_price', 'stock_count', 'image', 'is_active']
    classes = []  
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter choices based on the parent product"""
        if db_field.name == "color":
            # Get the product from the parent instance
            parent_id = request.resolver_match.kwargs.get('object_id')
            if parent_id:
                try:
                    product = Product.objects.get(id=parent_id)
                    kwargs["queryset"] = product.available_colors.all()
                except Product.DoesNotExist:
                    pass
        elif db_field.name == "size":
            parent_id = request.resolver_match.kwargs.get('object_id')
            if parent_id:
                try:
                    product = Product.objects.get(id=parent_id)
                    kwargs["queryset"] = product.available_sizes.all()
                except Product.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)




class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Only show variations inline if product has variations enabled
    def get_inline_instances(self, request, obj=None):
        inlines = [ProductImagesAdmin(self.model, self.admin_site)]
        
        # Only add variations inline if editing an existing product with variations
        if obj and obj.has_variations:
            inlines.append(ProductVariationInline(self.model, self.admin_site))
        
        return inlines
    
    list_editable = ['title', 'price', 'featured', 'product_status', 'has_variations']
    list_display = [
        'user', 'title', 'product_image', 'price', 
        'has_variations',  # Added this
        'mini_subcategory', 'vendor', 'featured', 
        'product_status', 'pid'
    ]
    
    list_filter = [
        'mini_subcategory__subcategory__category',
        'mini_subcategory__subcategory',
        'mini_subcategory',
        'product_status',
        'featured',
        'has_variations',  # Added this
    ]
    
    search_fields = ['title', 'mini_subcategory__title', 'sku']
    
    # Define fieldsets to organize the form better
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'image', 'description', 
                    'mini_subcategory', 'vendor', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'old_price', 'has_deal', 'deal_end_date')
        }),
        ('Variations Settings', {
            'fields': ('has_variations', 'available_colors', 'available_sizes'),
            'classes': ('collapse',),  # Collapsible section
            'description': 'Enable variations and select available colors/sizes'
        }),
        ('Inventory & Status', {
            'fields': ('stock_count', 'product_status', 'status', 
                    'in_stock', 'featured', 'digital', 'sku')
        }),
        ('Specifications', {
            'fields': ('specifications', 'type'),
            'classes': ('collapse',),
        }),
    )
    
    # Filter available_colors and available_sizes in form
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "available_colors":
            kwargs["queryset"] = Color.objects.all().order_by('name')
        elif db_field.name == "available_sizes":
            kwargs["queryset"] = Size.objects.all().order_by('name')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    # Add action to enable/disable variations for multiple products
    actions = ['enable_variations', 'disable_variations']
    
    def enable_variations(self, request, queryset):
        updated = queryset.update(has_variations=True)
        self.message_user(request, f'{updated} product(s) now have variations enabled.')
    enable_variations.short_description = "Enable variations for selected products"
    
    def disable_variations(self, request, queryset):
        updated = queryset.update(has_variations=False)
        self.message_user(request, f'{updated} product(s) now have variations disabled.')
    disable_variations.short_description = "Disable variations for selected products"

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

