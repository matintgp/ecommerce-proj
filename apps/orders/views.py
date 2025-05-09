from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem, Cart, CartItem, Coupon
from .serializers import (
    OrderSerializer, OrderItemSerializer, 
    CartSerializer, CartItemSerializer, CouponSerializer
)
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class OrderViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing user orders
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Get all orders",
        operation_description="Retrieve all orders for the current user"
    )
    @action(detail=False, methods=['get'], url_path='')
    def list_orders(self, request):
        """دریافت تمام سفارش‌های کاربر"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Get order details",
        operation_description="Retrieve details for a specific order"
    )
    @action(detail=True, methods=['get'], url_path='')
    def get_order(self, request, pk=None):
        """دریافت جزئیات یک سفارش"""
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Cancel order",
        operation_description="Cancel an order that hasn't been shipped yet"
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """لغو سفارش"""
        order = self.get_object()
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()
            return Response({"status": "سفارش با موفقیت لغو شد"})
        return Response(
            {"error": "سفارش‌هایی که ارسال شده یا تحویل داده شده‌اند قابل لغو نیستند"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @swagger_auto_schema(
        operation_summary="Update payment status",
        operation_description="Update order status after successful payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['payment_status', 'transaction_id'],
            properties={
                'payment_status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['paid', 'failed'],
                    description='Payment status'
                ),
                'transaction_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Payment transaction ID'
                )
            }
        )
    )
    @action(detail=True, methods=['post'], url_path='payment')
    def update_payment(self, request, pk=None):
        """به‌روزرسانی وضعیت پرداخت سفارش"""
        order = self.get_object()
        payment_status = request.data.get('payment_status')
        transaction_id = request.data.get('transaction_id')
        
        if payment_status not in ['paid', 'failed']:
            return Response(
                {"error": "وضعیت پرداخت نامعتبر است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status != 'pending':
            return Response(
                {"error": "فقط سفارش‌های در انتظار پرداخت قابل به‌روزرسانی هستند"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if payment_status == 'paid':
            order.status = 'processing'
            order.is_paid = True
            order.transaction_id = transaction_id
            order.payment_date = timezone.now()
            order.save()
            return Response({"status": "پرداخت با موفقیت انجام شد"})
        else:
            return Response({"status": "پرداخت ناموفق بود"})
    
    @swagger_auto_schema(
        operation_summary="Track order",
        operation_description="Get tracking information for an order"
    )
    @action(detail=True, methods=['get'], url_path='track')
    def track_order(self, request, pk=None):
        """پیگیری وضعیت سفارش"""
        order = self.get_object()
        
        tracking_info = {
            "order_id": order.id,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "is_paid": order.is_paid,
            "payment_date": order.payment_date,
            "shipping_date": None,
            "estimated_delivery": None,
        }
        
        return Response(tracking_info)


class CartViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing user shopping carts
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Get user's cart",
        operation_description="Retrieves the current user's shopping cart with all items"
    )
    @action(detail=False, methods=['get'], url_path='')
    def get_cart(self, request):
        """دریافت سبد خرید کاربر"""
        # Get or create a cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add product to cart",
        operation_description="Add a product to the user's cart or increase quantity if already exists",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id', 'quantity'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity to add')
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        """افزودن محصول به سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            return Response(
                {"error": "تعداد محصول باید بیشتر از صفر باشد"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if item already exists in cart
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.quantity += quantity
            item.save()
        except CartItem.DoesNotExist:
            # Create new cart item
            CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                quantity=quantity
            )
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update cart item",
        operation_description="Update the quantity of a product in the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quantity'],
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='New quantity')
            }
        )
    )
    @action(detail=True, methods=['put'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None, **kwargs):
        """به‌روزرسانی تعداد محصول در سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        quantity = int(request.data.get('quantity', 1))
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            
            if quantity <= 0:
                # Remove item if quantity is 0 or negative
                item.delete()
            else:
                item.quantity = quantity
                item.save()
                
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Remove item from cart",
        operation_description="Remove a specific item from the user's cart"
    )
    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None, **kwargs):
        """حذف محصول از سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Clear cart",
        operation_description="Remove all items from the user's cart"
    )
    @action(detail=False, methods=['delete'], url_path='items')
    def clear_cart(self, request):
        """پاک کردن تمام محصولات سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Checkout",
        operation_description="Create an order from the cart items",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['address_id', 'payment_method'],
            properties={
                'address_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Shipping address ID'),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment method'),
                'coupon_code': openapi.Schema(type=openapi.TYPE_STRING, description='Optional coupon code')
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """تبدیل سبد خرید به سفارش"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        address_id = request.data.get('address_id')
        payment_method = request.data.get('payment_method')
        coupon_code = request.data.get('coupon_code')
        
        # Check for items in cart
        items = cart.items.all()
        if not items:
            return Response(
                {"error": "سبد خرید شما خالی است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in items)
        total = subtotal
        discount = 0
        
        # Apply coupon if provided
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                now = timezone.now()
                
                if (coupon.valid_from <= now <= coupon.valid_to and 
                    (not coupon.usage_limit or coupon.used_count < coupon.usage_limit)):
                    
                    # Calculate discount
                    if coupon.discount_type == 'percentage':
                        discount = subtotal * (coupon.discount_value / 100)
                    else:  # fixed amount
                        discount = coupon.discount_value
                        
                    # Ensure discount doesn't exceed subtotal
                    discount = min(discount, subtotal)
                    total = subtotal - discount
                    
                    # Update coupon usage
                    coupon.used_count += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                pass
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address_id=address_id,
            payment_method=payment_method,
            subtotal=subtotal,
            discount=discount,
            total=total,
            coupon_code=coupon_code if coupon_code and discount > 0 else None
        )
        
        # Add items to order
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                subtotal=item.product.price * item.quantity
            )
        
        # Clear the cart
        cart.items.all().delete()
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    
    
class CouponViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing discount coupons
    """
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        now = timezone.now()
        return Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
    
    @swagger_auto_schema(
        operation_summary="Validate coupon",
        operation_description="Check if a coupon code is valid and get discount information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='Coupon code'),
                'cart_total': openapi.Schema(
                    type=openapi.TYPE_NUMBER, 
                    description='Optional cart total to calculate the actual discount'
                )
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        """اعتبارسنجی کد تخفیف"""
        code = request.data.get('code')
        cart_total = float(request.data.get('cart_total', 0))
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response(
                {"valid": False, "message": "کد تخفیف نامعتبر است"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            return Response(
                {"valid": False, "message": "کد تخفیف منقضی شده است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return Response(
                {"valid": False, "message": "حداکثر استفاده از این کد تخفیف به اتمام رسیده است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Calculate the actual discount if cart_total is provided
        discount_amount = 0
        if cart_total > 0:
            if coupon.discount_type == 'percentage':
                discount_amount = cart_total * (coupon.discount_value / 100)
            else:  # fixed amount
                discount_amount = min(coupon.discount_value, cart_total)
        
        response_data = {
            "valid": True,
            "coupon": CouponSerializer(coupon).data,
        }
        
        if cart_total > 0:
            response_data.update({
                "discount_amount": discount_amount,
                "total_after_discount": cart_total - discount_amount
            })
            
        return Response(response_data)
    
    @swagger_auto_schema(
        operation_summary="Apply coupon to cart",
        operation_description="Apply a coupon to the user's cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='Coupon code')
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='apply')
    def apply_to_cart(self, request):
        """اعمال کد تخفیف روی سبد خرید"""
        code = request.data.get('code')
        
        # Get the user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "سبد خرید یافت نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate coupon
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response(
                {"valid": False, "message": "کد تخفیف نامعتبر است"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            return Response(
                {"valid": False, "message": "کد تخفیف منقضی شده است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return Response(
                {"valid": False, "message": "حداکثر استفاده از این کد تخفیف به اتمام رسیده است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate cart total
        items = cart.items.all()
        cart_total = sum(item.product.price * item.quantity for item in items)
        
        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount_amount = cart_total * (coupon.discount_value / 100)
        else:  # fixed amount
            discount_amount = min(coupon.discount_value, cart_total)
        
        # Return discount information
        return Response({
            "valid": True,
            "coupon": CouponSerializer(coupon).data,
            "cart_total": cart_total,
            "discount_amount": discount_amount,
            "total_after_discount": cart_total - discount_amount
        })