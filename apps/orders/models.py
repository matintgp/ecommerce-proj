from django.db import models
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.db.models import Q
from apps.products.models import Color as ProductColor, Size as ProductSize








class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Shipping address
    shipping_address = models.ForeignKey('accounts.UserAddress', on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    
    # Payment information
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Promo code
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = get_random_string(10).upper()
        
        # Calculate total
        self.total = self.subtotal + self.shipping_cost + self.tax - self.discount
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.email if self.user else 'Guest'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    
    # Store product details at time of purchase (in case product changes later)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    selected_color_name = models.CharField(max_length=50, blank=True, null=True)
    selected_size_name = models.CharField(max_length=50, blank=True, null=True)
    # ForeignKey to ProductColor and ProductSize models
    selected_color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True)
    selected_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    
    

    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.subtotal = self.product_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        color_size_info = ""
        if self.selected_color_name:
            color_size_info += f" - Color: {self.selected_color_name}"
        if self.selected_size_name:
            color_size_info += f" - Size: {self.selected_size_name}"
        return f"{self.quantity}x {self.product_name}{color_size_info} in Order #{self.order.order_number}"
    

class Cart(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For guest users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart'
            ),
            models.UniqueConstraint(
                fields=['session_id'],
                condition=models.Q(session_id__isnull=False),
                name='unique_session_cart'
            ),
        ]

    def __str__(self):
        return f"Cart: {self.user.email if self.user else self.session_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for selected color and size
    selected_color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True)
    selected_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # Ensure uniqueness for product with specific color and size in the cart
        unique_together = ('cart', 'product', 'selected_color', 'selected_size')

    def __str__(self):
        color_size_info = ""
        if self.selected_color:
            color_size_info += f" - Color: {self.selected_color.name}"
        if self.selected_size:
            color_size_info += f" - Size: {self.selected_size.name}"
        return f"{self.quantity}x {self.product.name}{color_size_info} in {self.cart}"
    

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Discount amount
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_percentage = models.BooleanField(default=False)
    
    # Limitations
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Time constraints
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # None means unlimited
    used_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_to and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )