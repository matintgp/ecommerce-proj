from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    fields = ('product', 'product_name', 'product_price', 'quantity', 'subtotal')
    readonly_fields = ('product_name', 'product_price', 'subtotal')
    extra = 0
    can_delete = True 

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'order_number', 
        'user_email', 
        'status', 
        'payment_status', 
        'total', 
        'created_at',
        'shipping_address_summary'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'user']
    
    search_fields = [
        'order_number', 
        'user__email', 
        'user__username', 
        'user__first_name',
        'user__last_name',
        'shipping_address__address', 
        'shipping_address__city',
        'shipping_address__country',
        'shipping_address__postal_code',
        'transaction_id',
        'tracking_number'
    ]
    
    inlines = [OrderItemInline]
    list_per_page = 25
    readonly_fields = ('order_number', 'subtotal', 'total', 'created_at', 'updated_at', 'user_email_display')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'user_email_display', 'status', 'created_at', 'updated_at')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address',)
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'payment_date', 'promo_code', 'discount')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'total')
        }),
        ('Tracking Information', {
            'fields': ('tracking_number', 'shipped_at', 'delivered_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'User Email'

    def user_email_display(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email_display.short_description = 'User Email'

    def shipping_address_summary(self, obj):
        if obj.shipping_address:
            user_full_name = f"{obj.shipping_address.user.first_name} {obj.shipping_address.user.last_name}" if obj.shipping_address.user else "Guest"
            return f"{user_full_name}, {obj.shipping_address.address}, {obj.shipping_address.city}"
        return "N/A"
    shipping_address_summary.short_description = 'Shipping Address'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'shipping_address', 'shipping_address__user')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'product_name', 'quantity', 'product_price', 'subtotal')
    list_filter = ('order__status', 'order__created_at')
    
    search_fields = [
        'order__order_number', 
        'product_name', 
        'product__name',
        'order__user__email',
        'order__user__username'
    ]
    
    raw_id_fields = ['order', 'product']
    readonly_fields = ('subtotal',)

    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:orders_order_change", args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', link, obj.order.order_number)
    order_link.short_description = 'Order'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user', 'product')

class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'session_id', 'created_at', 'updated_at', 'item_count')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('user__email', 'user__username', 'session_id')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email if obj.user else 'Guest Cart'
    user_email.short_description = 'User/Session'

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Item Count'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_info', 'product', 'quantity', 'added_at')
    list_filter = ('cart__user', 'added_at')
    search_fields = ('cart__user__email', 'product__name', 'cart__session_id')
    raw_id_fields = ['cart', 'product']

    def cart_info(self, obj):
        if obj.cart.user:
            return f"Cart for {obj.cart.user.email}"
        return f"Guest Cart ({obj.cart.session_id[:8]}...)" if obj.cart.session_id else "Guest Cart"
    cart_info.short_description = 'Cart'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'cart__user', 'product')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'description_summary', 
        'amount_display', 
        'is_active', 
        'valid_from', 
        'valid_to', 
        'usage_limit', 
        'used_count',
        'min_purchase'
    )
    list_filter = ('is_active', 'is_percentage', 'valid_from', 'valid_to', 'created_at')
    search_fields = ('code', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Details', {
            'fields': ('amount', 'is_percentage', 'max_discount')
        }),
        ('Limitations & Validity', {
            'fields': ('min_purchase', 'valid_from', 'valid_to', 'usage_limit', 'used_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    actions = ['activate_coupons', 'deactivate_coupons']

    def description_summary(self, obj):
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description
    description_summary.short_description = 'Description'

    def amount_display(self, obj):
        if obj.is_percentage:
            return f"{obj.amount}%"
        return f"${obj.amount}"  
    amount_display.short_description = 'Discount'

    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کوپن فعال شد.')
    activate_coupons.short_description = "فعال کردن کوپن‌های انتخاب شده"

    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کوپن غیرفعال شد.')
    deactivate_coupons.short_description = "غیرفعال کردن کوپن‌های انتخاب شده"

    def get_queryset(self, request):
        return super().get_queryset(request)