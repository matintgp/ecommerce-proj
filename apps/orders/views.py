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
from .serializers import *



















class OrderViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing user orders
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 

    def get_serializer_class(self):
        if self.action == 'cancel':
            return OrderUpdateSerializer
        elif self.action == 'update_payment':
            return PaymentUpdateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user)
        return Order.objects.none() # یا مدیریت کاربر مهمان اگر لازم است
    
    @swagger_auto_schema(
        operation_summary="Get all orders",
        operation_description="Retrieve all orders for the current user",
        tags=["Orders"]
    )
    @action(detail=False, methods=['get'], url_path='')
    def list_orders(self, request):
        """دریافت تمام سفارش‌های کاربر"""
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
        """دریافت جزئیات یک سفارش"""
        order = get_object_or_404(self.get_queryset(), pk=pk) # استفاده از get_queryset برای امنیت
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Cancel order",
        operation_description="Cancel an order that hasn't been shipped yet. Allowed statuses for cancellation: 'pending', 'processing'.",
        # request_body=OrderUpdateSerializer, # بدنه درخواست برای کنسل کردن لازم نیست، مگر اینکه بخواهید دلیلی ارسال کنید
        responses={
            200: openapi.Response("Order cancelled successfully"),
            400: openapi.Response("Order cannot be cancelled"),
            404: openapi.Response("Order not found")
        },
        tags=["Orders"]
    )
    @action(detail=True, methods=['post'], url_path='cancel') 
    def cancel(self, request, pk=None):
        """لغو سفارش"""
        order = get_object_or_404(self.get_queryset(), pk=pk)
        
        # وضعیت‌هایی که در آن‌ها می‌توان سفارش را لغو کرد
        cancellable_statuses = ['pending', 'processing'] 
        
        if order.status in cancellable_statuses:
            # بازگرداندن محصولات به انبار در صورت لغو (اگر قبلا کم شده)
            # این بخش نیاز به بررسی دقیق‌تر دارد که آیا در زمان ایجاد سفارش از انبار کم شده یا در زمان پرداخت
            # فرض می‌کنیم در زمان ایجاد سفارش (checkout) از انبار کم شده است
            with transaction.atomic():
                order.status = 'cancelled'
                order.save(update_fields=['status'])

                # بازگرداندن آیتم‌ها به انبار
                for item in order.items.all():
                    if item.product: # بررسی اینکه محصول هنوز وجود دارد
                        product_to_update = item.product
                        product_to_update.stock += item.quantity
                        product_to_update.save(update_fields=['stock'])
                
                # اگر کوپنی استفاده شده بود، شمارنده آن را کاهش دهید (اختیاری و بسته به منطق کسب و کار)
                if order.promo_code and order.discount > 0:
                    try:
                        coupon = Coupon.objects.get(code=order.promo_code)
                        if coupon.used_count > 0:
                            coupon.used_count -= 1
                            coupon.save(update_fields=['used_count'])
                    except Coupon.DoesNotExist:
                        pass # اگر کوپن پیدا نشد، کاری انجام نده

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
        """به‌روزرسانی وضعیت پرداخت سفارش"""
        order = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = PaymentUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        requested_payment_status = serializer.validated_data['payment_status']
        transaction_id = serializer.validated_data.get('transaction_id') # دریافت transaction_id از سریالایزر

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
            if transaction_id: # اگر transaction_id ارسال شده بود
                order.transaction_id = transaction_id 
            order.payment_date = timezone.now() # تنظیم تاریخ پرداخت
            
            # اضافه کردن transaction_id و payment_date به update_fields
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

    
    # ...existing code...
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
        """پیگیری وضعیت سفارش"""
        order = get_object_or_404(self.get_queryset(), pk=pk)
        
        # محاسبه تاریخ تخمینی تحویل (مثال ساده)
        estimated_delivery_date = None
        if order.shipped_at:
            estimated_delivery_date = order.shipped_at + timezone.timedelta(days=3) # فرض ۳ روز برای تحویل
        
        tracking_info = {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "status_display": order.get_status_display(),
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "is_paid": order.payment_status == 'paid', 
            "payment_method": order.payment_method,
            "payment_date": order.payment_date, # اکنون این فیلد باید وجود داشته باشد
            "transaction_id": order.transaction_id, # اضافه کردن transaction_id به اطلاعات پیگیری
            "shipping_address": OrderSerializer(order).data.get('shipping_address_details'), 
            "tracking_number": order.tracking_number,
            "shipped_at": order.shipped_at,
            "delivered_at": order.delivered_at,
            "estimated_delivery": estimated_delivery_date.strftime('%Y-%m-%d') if estimated_delivery_date else None,
            "items": OrderItemSerializer(order.items.all(), many=True).data 
        }
        
        return Response(tracking_info)


class CartViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing user shopping carts
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    
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
        # Avoid error when generating Swagger docs
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
        """دریافت سبد خرید کاربر"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add product to cart",
        operation_description="Add a product to the user's cart or increase quantity if already exists",
        request_body=CartItemAddSerializer,
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        """افزودن محصول به سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemAddSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
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
        
        result_serializer = CartSerializer(cart)
        return Response(result_serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update cart item",
        operation_description="Update the quantity of a product in the cart",
        request_body=CartItemUpdateSerializer,
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['put'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None, **kwargs):
        """به‌روزرسانی تعداد محصول در سبد خرید"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        quantity = serializer.validated_data['quantity']
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.quantity = quantity
            item.save()
                
            result_serializer = CartSerializer(cart)
            return Response(result_serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"status": "error", "message": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Remove item from cart",
        operation_description="Remove a specific item from the user's cart",
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None, **kwargs):
        """حذف محصول از سبد خرید"""
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
        """پاک کردن تمام محصولات سبد خرید"""
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
        """تبدیل سبد خرید به سفارش"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CheckoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        address_id = serializer.validated_data['address_id']
        payment_method = "credit card" # یا هر روش پیش‌فرض دیگر
        coupon_code = serializer.validated_data.get('coupon_code', '').strip()
        
        items = cart.items.all()
        if not items:
            return Response(
                {"status": "error", "message": "سبد خرید شما خالی است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- BEGIN STOCK CHECK ---
        for item in items:
            if item.product.stock < item.quantity:
                return Response(
                    {"status": "error", "message": f"محصول '{item.product.name}' موجودی کافی ندارد."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # --- END STOCK CHECK ---
        
        subtotal = sum(item.product.price * item.quantity for item in items)
        total = subtotal 
        discount = Decimal('0.00') # مقدار اولیه تخفیف
        applied_coupon_object = None

        print(f"Checkout initiated. Subtotal: {subtotal}, Coupon Code: '{coupon_code}'")

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                now = timezone.now()
                print(f"Coupon found: {coupon.code}, Amount: {coupon.amount}, Is Percentage: {coupon.is_percentage}")
                print(f"Valid from: {coupon.valid_from}, Valid to: {coupon.valid_to}, Now: {now}")
                print(f"Usage limit: {coupon.usage_limit}, Used count: {coupon.used_count}")
                print(f"Min purchase: {coupon.min_purchase}")

                is_valid_date = coupon.valid_from <= now <= coupon.valid_to
                is_valid_usage = not coupon.usage_limit or coupon.used_count < coupon.usage_limit
                is_valid_min_purchase = not coupon.min_purchase or subtotal >= coupon.min_purchase
                
                print(f"Is valid date: {is_valid_date}, Is valid usage: {is_valid_usage}, Is valid min purchase: {is_valid_min_purchase}")

                if is_valid_date and is_valid_usage and is_valid_min_purchase:
                    if coupon.is_percentage:
                        # مطمئن شوید که coupon.amount و 100 به عنوان Decimal در نظر گرفته می‌شوند
                        discount_percentage = coupon.amount / Decimal('100.0')
                        calculated_discount = subtotal * discount_percentage
                    else:
                        calculated_discount = coupon.amount
                    
                    # اعمال حداکثر تخفیف اگر تعریف شده باشد
                    if coupon.max_discount and coupon.max_discount > 0:
                        discount = min(calculated_discount, coupon.max_discount)
                    else:
                        discount = calculated_discount
                    
                    # اطمینان از اینکه تخفیف از کل مبلغ بیشتر نشود
                    discount = min(discount, subtotal)
                    total = subtotal - discount
                    applied_coupon_object = coupon # ذخیره کوپن برای افزایش شمارنده استفاده
                    print(f"Discount calculated: {discount}, New total: {total}")
                else:
                    print("Coupon conditions not met.")
            except Coupon.DoesNotExist:
                print(f"Coupon with code '{coupon_code}' not found or not active.")
                pass # اگر کوپن پیدا نشد یا فعال نبود، تخفیف 0 باقی می‌ماند
        
        try:
            with transaction.atomic(): # شروع تراکنش
                order = Order.objects.create(
                    user=request.user,
                    shipping_address_id=address_id,
                    payment_method=payment_method,
                    subtotal=subtotal,
                    discount=discount, # مقدار تخفیف محاسبه شده
                    total=total,
                    promo_code=applied_coupon_object.code if applied_coupon_object and discount > 0 else None
                )
                
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        product_price=item.product.price,
                        quantity=item.quantity,
                        subtotal=item.product.price * item.quantity
                    )
                    
                    # --- BEGIN STOCK DEDUCTION ---
                    product_to_update = item.product
                    product_to_update.stock -= item.quantity
                    product_to_update.save(update_fields=['stock'])
                    # --- END STOCK DEDUCTION ---

                if applied_coupon_object and discount > 0:
                    applied_coupon_object.used_count += 1
                    applied_coupon_object.save(update_fields=['used_count'])
                    print(f"Coupon '{applied_coupon_object.code}' usage count incremented.")
                
                cart.items.all().delete() # پاک کردن سبد خرید
                print("Checkout successful. Order created, stock updated, cart cleared.")
                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error during checkout transaction: {str(e)}") # لاگ کردن خطا
            return Response(
                {"status": "error", "message": "خطایی در هنگام پردازش سفارش رخ داد. لطفا دوباره تلاش کنید."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Decrease item quantity in cart",
        operation_description="Decrease the quantity of a specific item in the user's cart by a specified amount. If quantity becomes zero or less, the item is removed.",
        request_body=CartItemQuantitySerializer, # استفاده از سریالایزر جدید
        responses={200: CartSerializer()},
        tags=["Cart"]
    )
    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/decrease')
    def decrease_item_quantity(self, request, item_id=None, **kwargs):
        """کم کردن تعداد یک محصول در سبد خرید"""
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
                # اگر تعداد کم شده بیشتر یا مساوی تعداد فعلی باشد، آیتم را حذف کن
                item.delete()
                
            result_serializer = CartSerializer(cart)
            return Response(result_serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"status": "error", "message": "آیتم در سبد خرید پیدا نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class CouponViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing discount coupons
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    
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
        """اعتبارسنجی کد تخفیف"""
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
            
        # Calculate the actual discount if cart_total is provided
        discount_amount = 0
        if cart_total > 0:
            if coupon.is_percentage:
                discount_amount = cart_total * (coupon.amount / 100)
            else:  # fixed amount
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
        """اعمال کد تخفیف روی سبد خرید"""
        serializer = CouponValidateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        code = serializer.validated_data['code']
        
        # Get the user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"status": "error", "message": "سبد خرید یافت نشد"}, 
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
        if coupon.is_percentage:
            discount_amount = cart_total * (coupon.amount / 100)
        else:  # fixed amount
            discount_amount = min(coupon.amount, cart_total)
        
        # Return discount information
        return Response({
            "valid": True,
            "coupon": CouponSerializer(coupon).data,
            "cart_total": int(cart_total),
            "discount_amount": int(discount_amount),
            "total_after_discount": int(cart_total - discount_amount)
        })