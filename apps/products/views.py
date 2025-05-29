from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the review.
        return obj.user == request.user


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related(
        'reviews', # برای بهینه‌سازی کوئری نظرات
        'size',    # نام فیلد ManyToMany در مدل Product
        'color',   # نام فیلد ManyToMany در مدل Product
        'images',
        'specifications'
    ).select_related('category', 'brand', 'gender') # برای بهینه‌سازی کوئری ForeignKey
    serializer_class = ProductSerializer
    http_method_names = ['get']
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination for this viewset
    page_size = 1000  # Set a large page size to avoid pagination
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="List all products",
        operation_description="Returns a list of all available products in the store"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    

    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Retrieve product details",
        operation_description="Get detailed information about a specific product"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ['get']
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="List all categories",
        operation_description="Returns a list of all product categories"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Retrieve category details",
        operation_description="Get detailed information about a specific category"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    


    
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    http_method_names = ['get']
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    
    @swagger_auto_schema(
        tags=['Brands'],
        operation_summary="List all brands",
        operation_description="Returns a list of all product brands"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Brands'],
        operation_summary="Retrieve brand details",
        operation_description="Get detailed information about a specific brand"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    



class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['product', 'rating']
    search_fields = ['title', 'comment']
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = None
    
    def get_queryset(self):
        # حالا که همه نظرات خودکار تایید می‌شوند، می‌توانیم همه را نمایش دهیم
        # اما اگر بخواهید فقط ادمین ها نظرات تایید نشده را ببینند:
        if hasattr(self.request, 'user') and self.request.user.is_staff:
            return Review.objects.all().select_related('user', 'product')
        return Review.objects.filter(is_approved=True).select_related('user', 'product')
    
    def get_permissions(self):
        """
        تنظیم مجوزها بر اساس عمل
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="List reviews",
        operation_description="Returns a list of product reviews. All reviews are automatically approved.",
        manual_parameters=[
            openapi.Parameter(
                'product', 
                openapi.IN_QUERY, 
                description="Filter reviews by product ID", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'rating', 
                openapi.IN_QUERY, 
                description="Filter reviews by rating (1-5)", 
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Create review",
        operation_description="Add a new review for a product. Authentication required. One review per product per user. Reviews are automatically approved.",
        request_body=ReviewSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Retrieve review",
        operation_description="Get detailed information about a specific review"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Partial update review",
        operation_description="Update one or more fields of an existing review. Only review owner can edit."
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Delete review",
        operation_description="Remove a review from the system. Only review owner or staff can delete."
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # تایید خودکار نظر هنگام ایجاد
        serializer.save(user=self.request.user, is_approved=True)

    def perform_update(self, serializer):
        # نظر همچنان تایید شده باقی بماند هنگام ویرایش
        serializer.save(is_approved=True)
        
        
        
        
        
        

class WishlistViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
    ):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']
    pagination_class = None
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="List wishlist items",
        operation_description="Returns a list of products in the user's wishlist. Authentication required."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    # @swagger_auto_schema(
    #     tags=["Wishlist"],
    #     operation_summary="Add item to wishlist",
    #     operation_description="Add a product to the user's wishlist. Authentication required.",
    #     request_body=WishlistCreateSerializer
    # )
    # def create(self, request, *args, **kwargs):
    #     return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Retrieve wishlist item",
        operation_description="Get detailed information about a specific wishlist item"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    # @swagger_auto_schema(
    #     tags=["Wishlist"],
    #     operation_summary="Remove from wishlist",
    #     operation_description="Remove a product from the user's wishlist"
    # )
    # def destroy(self, request, *args, **kwargs):
    #     return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Toggle wishlist",
        operation_description="Add or remove a product from wishlist. If exists, remove it; if not, add it.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID')
            },
            required=['product_id']
        )
    )
    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_wishlist(self, request):
        """تغییر وضعیت محصول در wishlist"""
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {"status": "error", "message": "product_id الزامی است"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"status": "error", "message": "محصول یافت نشد"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, 
            product=product
        )
        
        if created:
            return Response({
                "status": "success", 
                "message": "محصول به لیست علاقه‌مندی‌ها اضافه شد",
                "action": "added",
                "wishlist_item": WishlistSerializer(wishlist_item).data
            })
        else:
            wishlist_item.delete()
            return Response({
                "status": "success", 
                "message": "محصول از لیست علاقه‌مندی‌ها حذف شد",
                "action": "removed"
            })
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WishlistCreateSerializer
        return WishlistSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)