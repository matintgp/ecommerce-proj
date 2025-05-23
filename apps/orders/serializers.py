from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem, Coupon
from apps.products.serializers import ProductSerializer
from django.utils import timezone
from apps.products.serializers import ProductSerializer, ColorSerializer as ProductColorSerializer, SizeSerializer as ProductSizeSerializer
from apps.products.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal',
            'selected_color_name', 'selected_size_name',
            'selected_color', 'selected_size'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address_details = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'status', 'status_display', 'shipping_address', 
                 'shipping_address_details', 'payment_method', 'payment_status', 'subtotal', 
                 'shipping_cost', 'tax', 'discount', 'total', 'items', 'created_at', 
                 'tracking_number', 'shipped_at', 'delivered_at']
        read_only_fields = ['order_number', 'total', 'user']
    
    def get_shipping_address_details(self, obj):
        if obj.shipping_address:
            user_full_name = f"{obj.shipping_address.user.first_name} {obj.shipping_address.user.last_name}"
            return {
                "full_name": user_full_name,
                "address": obj.shipping_address.address,
                "country": obj.shipping_address.country,
                "city": obj.shipping_address.city,
                "postal_code": obj.shipping_address.postal_code,
                "email": obj.shipping_address.user.email
            }
        return None


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        

class PaymentUpdateSerializer(serializers.Serializer):
    payment_status = serializers.ChoiceField(choices=['paid', 'failed'])
    transaction_id = serializers.CharField(max_length=100)

    def validate_payment_status(self, value):
        if value not in ['paid', 'failed']:
            raise serializers.ValidationError("وضعیت پرداخت باید 'paid' یا 'failed' باشد")
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    selected_color = ProductColorSerializer(read_only=True) # Display color details
    selected_size = ProductSizeSerializer(read_only=True)   # Display size details
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_details', 'quantity', 'added_at',
            'selected_color', 'selected_size' # Add new fields
        ]
        read_only_fields = ['added_at']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد محصول باید بیشتر از صفر باشد")
        return value


class CartItemAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    color_id = serializers.IntegerField(required=False, allow_null=True) 
    size_id = serializers.IntegerField(required=False, allow_null=True)   
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد محصول باید بیشتر از صفر باشد")
        return value

    def validate(self, data):
        # Optional: Validate that the selected color and size are valid for the product
        # This requires querying the Product model and its available colors/sizes
        product_id = data.get('product_id')
        color_id = data.get('color_id')
        size_id = data.get('size_id')

        try:
            product = Product.objects.get(id=product_id)
            if color_id and not product.color.filter(id=color_id).exists():
                raise serializers.ValidationError(f"رنگ انتخاب شده برای محصول '{product.name}' موجود نیست.")
            if size_id and not product.size.filter(id=size_id).exists():
                raise serializers.ValidationError(f"سایز انتخاب شده برای محصول '{product.name}' موجود نیست.")
        except Product.DoesNotExist:
            raise serializers.ValidationError("محصول مورد نظر یافت نشد.")
        # Add more validation if a product *must* have a color or size selected
        # For example, if product.color.exists() and color_id is None:
        #     raise serializers.ValidationError("برای این محصول باید رنگ انتخاب شود.")

        return data

class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد محصول باید بیشتر از صفر باشد")
        return value




class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد محصول باید بیشتر از صفر باشد")
        return value


class CartItemQuantitySerializer(serializers.Serializer): # سریالایزر جدید
    quantity = serializers.IntegerField(min_value=1) # تعداد برای کم کردن

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد برای کم کردن باید بیشتر از صفر باشد")
        return value



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_total(self, obj):
        try:
            total = sum(item.product.price * item.quantity for item in obj.items.all())
            return int(total)
        except:
            return 0
    
    def get_item_count(self, obj):
        return obj.items.count()


class CouponSerializer(serializers.ModelSerializer):
    discount_type = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'description', 'amount', 'is_percentage', 
                 'discount_type', 'min_purchase', 'max_discount', 'valid_from', 
                 'valid_to', 'is_active', 'is_valid']
    
    def get_discount_type(self, obj):
        return "درصد" if obj.is_percentage else "مبلغ ثابت"
    
    def get_is_valid(self, obj):
        now = timezone.now()
        return (
            obj.is_active and 
            obj.valid_from <= now <= obj.valid_to and
            (obj.usage_limit is None or obj.used_count < obj.usage_limit)
        )


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    # payment_method = serializers.CharField(max_length=50)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # def validate_payment_method(self, value):
    #     valid_methods = ['credit_card', 'bank_transfer', 'cod']
    #     if value not in valid_methods:
    #         raise serializers.ValidationError(f"روش پرداخت باید یکی از موارد {valid_methods} باشد")
    #     return value

