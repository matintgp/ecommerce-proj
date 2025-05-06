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

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()
            return Response({"status": "Order cancelled"})
        return Response(
            {"error": "Cannot cancel orders that have been shipped or delivered"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if user already has a cart
        try:
            cart = Cart.objects.get(user=self.request.user)
            return cart
        except Cart.DoesNotExist:
            return serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.quantity += quantity
            item.save()
        except CartItem.DoesNotExist:
            CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                quantity=quantity
            )
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        cart = self.get_object()
        address_id = request.data.get('address_id')
        payment_method = request.data.get('payment_method')
        
        # Create order from cart
        items = cart.items.all()
        if not items:
            return Response(
                {"error": "Cannot checkout with empty cart"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in items)
        
        # Create order
        order = Order.objects.create(
            user=self.request.user,
            shipping_address_id=address_id,
            payment_method=payment_method,
            subtotal=subtotal,
            total=subtotal,  # Will be recalculated in Order.save()
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
        
        return Response(OrderSerializer(order).data)

class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        now = timezone.now()
        return Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        coupon = get_object_or_404(Coupon, code=code, is_active=True)
        
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            return Response(
                {"valid": False, "message": "Coupon has expired"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return Response(
                {"valid": False, "message": "Coupon usage limit reached"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "valid": True,
            "coupon": CouponSerializer(coupon).data
        })