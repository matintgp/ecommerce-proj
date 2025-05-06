from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem, Coupon
from apps.products.serializers import ProductSerializer 


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'status', 'shipping_address', 
                 'payment_method', 'payment_status', 'subtotal', 'shipping_cost', 
                 'tax', 'discount', 'total', 'items', 'created_at']
        read_only_fields = ['order_number', 'total']

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_details', 'quantity', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'created_at', 'updated_at']
        read_only_fields = ['user']
    
    def get_total(self, obj):
        total = sum(item.product.price * item.quantity for item in obj.items.all())
        return total

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'description', 'amount', 'is_percentage',
                 'min_purchase', 'max_discount', 'valid_from', 'valid_to',
                 'is_active']