from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from decimal import Decimal

from .models import *  
from apps.products.models import Color as ProductColor, Size as ProductSize 

from .serializers import *



















class OrderViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    pagination_class = None
    
    def get_serializer_class(self):
        if self.action == 'cancel':
            return OrderUpdateSerializer
        elif self.action == 'update_payment':
            return PaymentUpdateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user)
        return Order.objects.none()  
    
    @swagger_auto_schema(
        operation_summary="Get all orders",
        operation_description="Retrieve all orders for the current user",
        tags=["Orders"]
    )
    @action(detail=False, methods=['get'], url_path='')
    def list_orders(self, request):
        queryset = self.get_queryset().order_by('-created_at')
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Get order details",
        operation_description="Retrieve details for a specific order",
        tags=["Orders"]
    )
    @action(detail=True, methods=['get'], url_path='')
    def get_order(self, request, pk=None):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Cancel order",
        operation_description="Cancel an order that hasn't been shipped yet. Allowed statuses for cancellation: 'pending', 'processing'.",
        responses={
            200: openapi.Response("Order cancelled successfully"),
            400: openapi.Response("Order cannot be cancelled"),
            404: openapi.Response("Order not found")
        },
        tags=["Orders"]
    )
    @action(detail=True, methods=['post'], url_path='cancel') 
    def cancel(self, request, pk=None):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        cancellable_statuses = ['pending', 'processing'] 
        
        if order.status in cancellable_statuses:
            with transaction.atomic():
                order.status = 'cancelled'
                order.save(update_fields=['status'])

                for item in order.items.all():
                    if item.product:
                        product_to_update = item.product
                        product_to_update.stock += item.quantity
                        product_to_update.save(update_fields=['stock'])
                
                if order.promo_code and order.discount > 0:
                    try:
                        coupon = Coupon.objects.get(code=order.promo_code)
                        if coupon.used_count > 0:
                            coupon.used_count -= 1
                            coupon.save(update_fields=['used_count'])
                    except Coupon.DoesNotExist:
                        pass 

            return Response({"status": "success", "message": "سفارش با موفقیت لغو شد."})
        
        return Response(
            {"status": "error", "message": f"سفارش با وضعیت '{order.get_status_display()}' قابل لغو نیست. فقط سفارش‌های در وضعیت 'در انتظار بررسی' یا 'در حال پردازش' قابل لغو هستند."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @swagger_auto_schema(
        operation_summary="Update payment status",
        operation_description="Update order's payment status. Typically used after a payment gateway response.",
        request_body=PaymentUpdateSerializer,
        responses={
            200: openapi.Response("Payment status updated successfully"),
            400: openapi.Response("Invalid request or order status"),
            404: openapi.Response("Order not found")
        },
        tags=["Orders"]
    )
    @action(detail=True, methods=['post'], url_path='payment')
    def update_payment(self, request, pk=None):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = PaymentUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        requested_payment_status = serializer.validated_data['payment_status']
        transaction_id = serializer.validated_data.get('transaction_id') 

        allowed_statuses_for_payment_update = ['pending'] 
        if order.status not in allowed_statuses_for_payment_update:
            return Response(
                {"status": "error", "message": f"وضعیت پرداخت برای سفارش با وضعیت '{order.get_status_display()}' قابل به‌روزرسانی نیست."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if requested_payment_status == 'paid':
            if order.payment_status == 'paid':
                return Response({"status": "info", "message": "سفارش قبلاً پرداخت شده است."}, status=status.HTTP_200_OK)

            order.payment_status = 'paid'
            order.status = 'processing' 
            if transaction_id: 
                order.transaction_id = transaction_id 
            order.payment_date = timezone.now() 
            
            update_fields_list = ['payment_status', 'status', 'payment_date']
            if transaction_id:
                update_fields_list.append('transaction_id')
            order.save(update_fields=update_fields_list) 
            
            return Response({"status": "success", "message": "پرداخت با موفقیت ثبت شد و سفارش در حال پردازش است."})
        elif requested_payment_status == 'failed':
            order.payment_status = 'failed'
            order.save(update_fields=['payment_status'])
            return Response({"status": "info", "message": "وضعیت پرداخت به 'ناموفق' تغییر کرد."})
        else:
            return Response({"status": "error", "message": "وضعیت پرداخت ارسال شده نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

    
    @swagger_auto_schema(
        operation_summary="Track order",
        operation_description="Get tracking information for a specific order.",
        responses={
            200: openapi.Response("Tracking information", examples={"application/json": {
                "order_id": 1, "order_number": "XYZ123", "status": "shipped", 
                "status_display": "ارسال شده", "is_paid": True, "payment_date": "2025-05-18T12:00:00Z",
                "tracking_number": "TRK789", "shipped_at": "2025-05-19T10:00:00Z",
                "estimated_delivery": "2025-05-22"
            }}),
            404: openapi.Response("Order not found")
        },
        tags=["Orders"]
    )
    @action(detail=True, methods=['get'], url_path='track')
    def track_order(self, request, pk=None):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        
        estimated_delivery_timestamp = None
        if order.shipped_at:
            estimated_delivery_date = order.shipped_at + timezone.timedelta(days=3)
            estimated_delivery_timestamp = int(calendar.timegm(estimated_delivery_date.utctimetuple()))
        
        tracking_info = {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "status_display": order.get_status_display(),
            "created_at": int(calendar.timegm(order.created_at.utctimetuple())),
            "updated_at": int(calendar.timegm(order.updated_at.utctimetuple())),
            "is_paid": order.payment_status == 'paid', 
            "payment_method": order.payment_method,
            "payment_date": int(calendar.timegm(order.payment_date.utctimetuple())) if order.payment_date else None,
            "transaction_id": order.transaction_id,
            "shipping_address": OrderSerializer(order).data.get('shipping_address_details'), 
            "tracking_number": order.tracking_number,
            "shipped_at": int(calendar.timegm(order.shipped_at.utctimetuple())) if order.shipped_at else None,
            "delivered_at": int(calendar.timegm(order.delivered_at.utctimetuple())) if order.delivered_at else None,
            "estimated_delivery": estimated_delivery_timestamp,
            "items": OrderItemSerializer(order.items.all(), many=True).data 
        }
        
        return Response(tracking_info)


class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    pagination_class = None
    
    def get_serializer_class(self):
        if self.action == 'add_item':
            return CartItemAddSerializer
        elif self.action == 'update_item':
            return CartItemUpdateSerializer
        elif self.action == 'checkout':
            return CheckoutSerializer
        elif self.action == 'decrease_item_quantity':
            return CartItemQuantitySerializer 
        return CartSerializer
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)
    
    
    @swagger_auto_schema(
        operation_summary="Get user's cart",
        operation_description="Retrieves the current user's shopping cart with all items",
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=False, methods=['get'], url_path='')
    def get_cart(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add product to cart",
        operation_description="Add a product to the user's cart or increase quantity if already exists. Specify color_id and size_id if applicable.",
        request_body=CartItemAddSerializer,
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemAddSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        color_id = serializer.validated_data.get('color_id')
        size_id = serializer.validated_data.get('size_id')
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"status": "error", "message": "محصول یافت نشد."}, 
                        status=status.HTTP_404_NOT_FOUND)
        
        selected_color_obj = None
        selected_size_obj = None
        
        if color_id:
            try:
                selected_color_obj = product.color.get(id=color_id)
            except ProductColor.DoesNotExist:
                return Response({"status": "error", "message": "رنگ انتخاب شده برای این محصول موجود نیست."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        if size_id:
            try:
                selected_size_obj = product.size.get(id=size_id)
            except ProductSize.DoesNotExist:
                return Response({"status": "error", "message": "سایز انتخاب شده برای این محصول موجود نیست."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        existing_item = None
        try:
            existing_item = CartItem.objects.get(
                cart=cart,
                product=product,
                selected_color=selected_color_obj,
                selected_size=selected_size_obj
            )
        except CartItem.DoesNotExist:
            pass
        
        current_cart_quantity = existing_item.quantity if existing_item else 0
        final_quantity = current_cart_quantity + quantity
        
        if final_quantity > product.stock:
            return Response({
                "status": "error", 
                "message": f"موجودی کافی نیست. موجودی انبار: {product.stock} عدد، موجودی در سبد شما: {current_cart_quantity} عدد، حداکثر قابل اضافه کردن: {max(0, product.stock - current_cart_quantity)} عدد"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if existing_item:
            existing_item.quantity = final_quantity
            existing_item.save(update_fields=['quantity', 'updated_at'])
        else:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
                selected_color=selected_color_obj,
                selected_size=selected_size_obj
            )
        
        result_serializer = CartSerializer(cart)
        return Response(result_serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update cart item quantity", 
        operation_description="Update the quantity of a product in the cart. To change color/size, remove and re-add the item.",
        request_body=CartItemUpdateSerializer, 
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['put'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        quantity = serializer.validated_data['quantity']
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            if quantity > item.product.stock:
                return Response({
                    "status": "error", 
                    "message": f"موجودی کافی نیست. موجودی انبار: {item.product.stock} عدد، حداکثر قابل انتخاب: {item.product.stock} عدد"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            item.quantity = quantity
            item.save(update_fields=['quantity', 'updated_at'])
                
            result_serializer = CartSerializer(cart)
            return Response(result_serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"status": "error", "message": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Remove item from cart",
        operation_description="Remove a specific item (product with specific color/size) from the user's cart",
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            result_serializer = CartSerializer(cart)
            return Response(result_serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"status": "error", "message": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Clear cart",
        operation_description="Remove all items from the user's cart",
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=False, methods=['delete'], url_path='items')
    def clear_cart(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        result_serializer = CartSerializer(cart)
        return Response(result_serializer.data)

    @swagger_auto_schema(
            operation_summary="Checkout",
            operation_description="Create an order from the cart items",
            request_body=CheckoutSerializer,
            responses={201: OrderSerializer()},
            tags=["Cart"]
    )
    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CheckoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        address_id = serializer.validated_data['address_id']
        payment_method = "credit card" 
        coupon_code = serializer.validated_data.get('coupon_code', '').strip()
        
        cart_items = cart.items.all()
        if not cart_items:
            return Response(
                {"status": "error", "message": "سبد خرید شما خالی است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        for cart_item_obj in cart_items: 
            if cart_item_obj.product.stock < cart_item_obj.quantity:
                return Response(
                    {"status": "error", "message": f"محصول '{cart_item_obj.product.name}' موجودی کافی ندارد."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        total = subtotal 
        discount = Decimal('0.00')
        applied_coupon_object = None

        print(f"Checkout initiated. Subtotal: {subtotal}, Coupon Code: '{coupon_code}'")

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                now = timezone.now()
                is_valid_date = coupon.valid_from <= now <= coupon.valid_to
                is_valid_usage = not coupon.usage_limit or coupon.used_count < coupon.usage_limit
                is_valid_min_purchase = not coupon.min_purchase or subtotal >= coupon.min_purchase
                
                if is_valid_date and is_valid_usage and is_valid_min_purchase:
                    if coupon.is_percentage:
                        discount_percentage = coupon.amount / Decimal('100.0')
                        calculated_discount = subtotal * discount_percentage
                    else:
                        calculated_discount = coupon.amount
                    
                    if coupon.max_discount and coupon.max_discount > 0:
                        discount = min(calculated_discount, coupon.max_discount)
                    else:
                        discount = calculated_discount
                    
                    discount = min(discount, subtotal) 
                    total = subtotal - discount
                    applied_coupon_object = coupon
            except Coupon.DoesNotExist:
                pass 
        
        try:
            with transaction.atomic(): 
                order = Order.objects.create(
                    user=request.user,
                    shipping_address_id=address_id,
                    payment_method=payment_method,
                    subtotal=subtotal,
                    discount=discount, 
                    total=total,
                    promo_code=applied_coupon_object.code if applied_coupon_object and discount > 0 else None
                )
                
                for cart_item_obj in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item_obj.product,
                        product_name=cart_item_obj.product.name,
                        product_price=cart_item_obj.product.price,
                        quantity=cart_item_obj.quantity,
                        subtotal=cart_item_obj.product.price * cart_item_obj.quantity,
                        selected_color_name=cart_item_obj.selected_color.name if cart_item_obj.selected_color else None,
                        selected_size_name=cart_item_obj.selected_size.name if cart_item_obj.selected_size else None
                    )
                    
                    product_to_update = cart_item_obj.product
                    product_to_update.stock -= cart_item_obj.quantity
                    product_to_update.save(update_fields=['stock'])

                if applied_coupon_object and discount > 0:
                    applied_coupon_object.used_count += 1
                    applied_coupon_object.save(update_fields=['used_count'])
                
                cart.items.all().delete() 
                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"status": "error", "message": f"خطایی در هنگام پردازش سفارش رخ داد: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Decrease item quantity in cart",
        operation_description="Decrease the quantity of a specific item (product with specific color/size) in the user's cart. If quantity becomes zero or less, the item is removed.",
        request_body=CartItemQuantitySerializer, 
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/decrease') 
    def decrease_item_quantity(self, request, item_id=None, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemQuantitySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        decrease_by = serializer.validated_data['quantity']

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            
            if item.quantity > decrease_by:
                item.quantity -= decrease_by
                item.save()
            else:
                item.delete()
                
            result_serializer = CartSerializer(cart)
            return Response(result_serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"status": "error", "message": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class CouponViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    pagination_class = None
    
    def get_serializer_class(self):
        if self.action == 'validate' or self.action == 'apply_to_cart':
            return CouponValidateSerializer
        return CouponSerializer
    
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
        request_body=CouponValidateSerializer,
        tags=["Coupons"]
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        code = serializer.validated_data['code']
        cart_total = float(serializer.validated_data.get('cart_total', 0))
        
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
            
        discount_amount = 0
        if cart_total > 0:
            if coupon.is_percentage:
                discount_amount = cart_total * (coupon.amount / 100)
            else:
                discount_amount = min(coupon.amount, cart_total)
        
        response_data = {
            "valid": True,
            "coupon": CouponSerializer(coupon).data,
        }
        
        if cart_total > 0:
            response_data.update({
                "discount_amount": int(discount_amount),
                "total_after_discount": int(cart_total - discount_amount)
            })
            
        return Response(response_data)
    
    @swagger_auto_schema(
        operation_summary="Apply coupon to cart",
        operation_description="Apply a coupon to the user's cart",
        request_body=CouponValidateSerializer,
        tags=["Coupons"]
    )
    @action(detail=False, methods=['post'], url_path='apply')
    def apply_to_cart(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        code = serializer.validated_data['code']
        
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"status": "error", "message": "سبد خرید یافت نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
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
        
        items = cart.items.all()
        cart_total = sum(item.product.price * item.quantity for item in items)
        if coupon.is_percentage:
            discount_amount = cart_total * (coupon.amount / 100)
        else: 
            discount_amount = min(coupon.amount, cart_total)
        
        return Response({
            "valid": True,
            "coupon": CouponSerializer(coupon).data,
            "cart_total": int(cart_total),
            "discount_amount": int(discount_amount),
            "total_after_discount": int(cart_total - discount_amount)
        })


