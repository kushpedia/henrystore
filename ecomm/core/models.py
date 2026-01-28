from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from taggit.managers import TaggableManager
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
from django.db.models import Avg
from decimal import Decimal


STATUS_CHOICE = (
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
)


STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("rejected", "Rejected"),
    ("in_review", "In Review"),
    ("published", "Published"),
)


RATING = (
    (5,  "★★★★★"),
    (4,  "★★★★☆"),
    (3,  "★★★☆☆"),
    (2,  "★★☆☆☆"),
    (1,  "★☆☆☆☆"),    
)


def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class Tags(models.Model):
    pass

class Category(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=200,
                        prefix="cat", alphabet="abcdefgh12345")
    title = models.CharField(max_length=100, default="Electronics")
    image = models.ImageField(upload_to="category", default="category.jpg")
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
    
    def product_count(self):
        # Count products through all subcategories and mini-subcategories
        count = 0
        for subcategory in self.subcategories.all():
            count += subcategory.product_count()
        return count
    
    def get_published_products(self, limit=8):
        """Get published products for this category"""
        return Product.objects.filter(
            mini_subcategory__subcategory__category=self,
            product_status="published"
        )[:limit]
    
    def __str__(self):
        return self.title
    

class SubCategory(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=200,
                        prefix="sub", alphabet="abcdefgh12345")
    title = models.CharField(max_length=100, default="Mobile Phones & Accessories")
    image = models.ImageField(upload_to="subcategory", default="subcategory.jpg")
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="subcategories"
    )
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Sub Categories"
        unique_together = ['category', 'title']  # Prevent duplicate subcategories in same category
    
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
    
    def product_count(self):
        # Count products through all mini-subcategories
        count = 0
        for mini_subcategory in self.mini_subcategories.all():
            count += mini_subcategory.product_count()
        return count
    
    def __str__(self):
        return f"{self.category.title} - {self.title}"

class MiniSubCategory(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=200,
                        prefix="mini", alphabet="abcdefgh12345")
    title = models.CharField(max_length=100, default="Smartphones")
    image = models.ImageField(upload_to="mini_subcategory", default="mini_subcategory.jpg")
    subcategory = models.ForeignKey(
        SubCategory, 
        on_delete=models.CASCADE, 
        related_name="mini_subcategories"
    )
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Mini Sub Categories"
        unique_together = ['subcategory', 'title']  # Prevent duplicate mini-subcategories in same subcategory
    
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
    
    def product_count(self):
        return Product.objects.filter(mini_subcategory=self).count()
    
    def get_full_path(self):
        return f"{self.subcategory.category.title} > {self.subcategory.title} > {self.title}"
    
    def __str__(self):
        return self.title


class Vendor(models.Model):
    vid = ShortUUIDField(unique=True, length=10, max_length=20,
                    prefix="ven", alphabet="abcdefgh12345")

    title = models.CharField(max_length=100, default="Nestify")
    image = models.ImageField(
        upload_to=user_directory_path, default="vendor.jpg")
    cover_image = models.ImageField(
        upload_to=user_directory_path, default="vendor.jpg")
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # description = models.TextField(null=True, blank=True, default="I am an Amazing Vendor")
    description = RichTextUploadingField(null=True, blank=True, default="I am an Amazing Vendor")
    

    address = models.CharField(max_length=100, default="123 Main Street.")
    contact = models.CharField(max_length=100, default="+123 (456) 789")
    chat_resp_time = models.CharField(max_length=100, default="100")
    shipping_on_time = models.CharField(max_length=100, default="100")
    authentic_rating = models.CharField(max_length=100, default="100")
    days_return = models.CharField(max_length=100, default="100")
    warranty_period = models.CharField(max_length=100, default="100")

    
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Vendors"

    def vendor_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))
    
    def get_average_rating(self):
        """Calculate average rating for all products from this vendor"""
        # Get all products of this vendor
        products = self.product.all()  # using related_name="product"
        
        # Get all reviews for these products
        from django.db.models import Avg
        average = ProductReview.objects.filter(
            product__in=products
        ).aggregate(average_rating=Avg('rating'))
        
        return average['average_rating'] if average['average_rating'] else 0
    
    def get_total_reviews_count(self):
        """Get total number of reviews for all products from this vendor"""
        products = self.product.all()
        return ProductReview.objects.filter(product__in=products).count()

    def __str__(self):
        return self.title

# Product variations#
class Color(models.Model):
    """Model to store available colors"""
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, help_text="Hex color code, e.g., #FF0000")
    
    def color_preview(self):
        return mark_safe(
            f'<div style="width: 30px; height: 30px; background-color: {self.hex_code}; border: 1px solid #ccc;"></div>'
        )
    
    def __str__(self):
        return self.name


class Size(models.Model):
    """Model to store available sizes"""
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    pid = ShortUUIDField(unique=True, length=10,
                        max_length=20, alphabet="abcdefgh12345")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    mini_subcategory = models.ForeignKey(
        MiniSubCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name="products"
    )
    
    

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, null=True, related_name="product")

    title = models.CharField(max_length=100, default="Sample Product")
    image = models.ImageField(
        upload_to=user_directory_path, default="product.jpg")
    # description = models.TextField(null=True, blank=True, default="This is the product")
    description = RichTextUploadingField(null=True, blank=True, default="This is the product")
    # description = CKEditor5Field(config_name='extends', null=True, blank=True)

    price = models.DecimalField(
        max_digits=12, decimal_places=2, default="0")
    old_price = models.DecimalField(
        max_digits=12, decimal_places=2, default="10000")

    # specifications = CKEditor5Field(config_name='extends', null=True, blank=True)
    specifications = models.TextField(null=True, blank=True)
    type = models.CharField(
        max_length=100, default="Generic", null=True, blank=True)
    stock_count = models.CharField(
        max_length=100, default="100", null=True, blank=True)
    
    tags = TaggableManager(blank=True)


    product_status = models.CharField(
        choices=STATUS, max_length=10, default="published")

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)

    sku = ShortUUIDField(unique=True, length=4, max_length=10,
                        prefix="sku", alphabet="1234567890")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    deal_end_date = models.DateTimeField(blank=True, null=True)
    has_deal = models.BooleanField(default=False)

    # variations
    has_variations = models.BooleanField(default=False)
    available_colors = models.ManyToManyField(Color, blank=True, related_name='products')
    available_sizes = models.ManyToManyField(Size, blank=True, related_name='products')


    class Meta:
        verbose_name_plural = "Products"

    def get_average_rating(self):
        """Get the average rating score for this product"""
        
        average = self.reviews.aggregate(average_rating=Avg('rating'))
        return average['average_rating'] if average['average_rating'] else 0
    
    def get_total_ratings(self):
        """Get the total number of ratings/reviews for this product"""
        return self.reviews.count()

    def get_category(self):
        """Get the top-level category"""
        if self.mini_subcategory:
            return self.mini_subcategory.subcategory.category
        return None
    
    def get_subcategory(self):
        """Get the subcategory"""
        if self.mini_subcategory:
            return self.mini_subcategory.subcategory
        return None
    
    def get_full_category_path(self):
        """Get full category path as string"""
        if self.mini_subcategory:
            return self.mini_subcategory.get_full_path()
        return "No category assigned"
    

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title

    def get_precentage(self):
        if self.old_price and self.old_price > 0:
            return int(((self.old_price - self.price)/(self.old_price)) * 100)
        return 0

class ProductImages(models.Model):
    images = models.ImageField(
        upload_to="product-images", default="product.jpg")
    product = models.ForeignKey(
        Product, related_name="p_images", on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Images"



        # variations 
class ProductVariation(models.Model):
    """Model for product variations (combinations of color, size, etc.)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Variation-specific details
    sku = ShortUUIDField(unique=True, length=8, max_length=12, 
                        prefix="var", alphabet="1234567890")
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    old_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    stock_count = models.IntegerField(default=100)
    image = models.ImageField(upload_to="variation-images", null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'color', 'size']
        verbose_name_plural = "Product Variations"
    
    def __str__(self):
        variation_name = f"{self.product.title}"
        if self.color:
            variation_name += f" - {self.color.name}"
        if self.size:
            variation_name += f" - {self.size.name}"
        return variation_name
    
    def get_final_price(self):
        """Return variation price if set, otherwise product price"""
        if self.price is not None:
            return self.price
        return self.product.price
    
    def get_final_old_price(self):
        """Return variation old price if set, otherwise product old price"""
        if self.old_price is not None:
            return self.old_price
        return self.product.old_price
    
    def is_in_stock(self):
        return self.stock_count > 0
    
    def variation_image(self):
        """Return variation image or product image"""
        if self.image:
            return self.image.url
        return self.product.image.url
    
    
############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################
############################################## Cart, Order, OrderITems and Address ##################################



class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=0, default="0")
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=30, default="processing")


    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)

    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    
    saved = models.DecimalField(max_digits=12, decimal_places=0, default="0")
    coupons = models.ManyToManyField("core.Coupon", blank=True)
    
    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_website_address = models.CharField(max_length=100, null=True, blank=True)
    
    sku = ShortUUIDField(null=True, blank=True, length=5,prefix="SKU", max_length=20, alphabet="1234567890")
    oid = ShortUUIDField(null=True, blank=True, length=8, max_length=20, alphabet="1234567890")
    stripe_payment_intent = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Cart Order"
        ordering = ['-date']

    def __str__(self):
        return f"Order #{self.oid} - {self.user.username}"
    
    def total_price(self):
        """Calculate total price from order items"""
        return self.cartorderitems_set.aggregate(
            total=models.Sum(models.F('price') * models.F('qty'))
        )['total'] or Decimal('0')
    @property
    def order_items(self):
        """Get all items for this order"""
        return self.items.all()
    
    @property
    def item_count(self):
        """Total number of items"""
        return self.items.aggregate(total=models.Sum('qty'))['total'] or 0
    
    @property
    def subtotal(self):
        """Subtotal before any discounts"""
        return self.items.aggregate(
            total=models.Sum(models.F('price') * models.F('qty'))
        )['total'] or Decimal('0')
    
    @property
    def final_total(self):
        """Final total after discounts"""
        subtotal = self.subtotal
        if self.saved:
            return subtotal - Decimal(str(self.saved))
        return subtotal
    
    def update_totals(self):
        """Update order totals from items"""
        items_total = self.subtotal
        self.price = items_total
        self.save()



class CartOrderItems(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=200)
    item = models.CharField(max_length=200)
    product_id=models.ForeignKey(Product, on_delete=models.SET_NULL, null=True,blank=True)
    variation = models.ForeignKey(
        ProductVariation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cart_items'
    )
    original_title = models.CharField(max_length=200, blank=True,null=True)
    image = models.CharField(max_length=200)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    total = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    
    color = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cart Order Item"
        
    def order_img(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image))
        
    def __str__(self):
        return f"{self.item} - Qty: {self.qty}"
    

############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################
############################################## Product Revew, wishlists, Address ##################################

class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="reviews")
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        if self.product:
            return self.product.title
        else:
            return f"review - {self.pk}"

    def get_rating(self):
        return self.rating


class wishlist_model(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "wishlists"

    def __str__(self):
        return self.product.title


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mobile = models.CharField(max_length=300, null=True)
    address = models.CharField(max_length=100, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Address"


class Coupon(models.Model):
    code = models.CharField(max_length=1000)
    discount = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code}"
    
