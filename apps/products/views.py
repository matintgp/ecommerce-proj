from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, Category, ProductImage, Review, Wishlist
from .serializers import ProductSerializer, CategorySerializer, ProductImageSerializer, ReviewSerializer, WishlistSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="List all products",
        operation_description="Returns a list of all available products in the store"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Create a new product",
        operation_description="Add a new product to the catalog"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Retrieve product details",
        operation_description="Get detailed information about a specific product"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Update product",
        operation_description="Update all fields of an existing product"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Partial update product",
        operation_description="Update one or more fields of an existing product"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Delete product",
        operation_description="Remove a product from the catalog"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="List all categories",
        operation_description="Returns a list of all product categories"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Create a category",
        operation_description="Add a new product category"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Retrieve category details",
        operation_description="Get detailed information about a specific category"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Update category",
        operation_description="Update all fields of an existing category"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Partial update category",
        operation_description="Update one or more fields of an existing category"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Categories'],
        operation_summary="Delete category",
        operation_description="Remove a category from the system"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="List all product images",
        operation_description="Returns a list of all product images"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Upload a product image",
        operation_description="Add a new image to a product"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Retrieve image details",
        operation_description="Get detailed information about a specific product image"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Update product image",
        operation_description="Update all fields of an existing product image"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Partial update product image",
        operation_description="Update one or more fields of an existing product image"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Products"],
        operation_summary="Delete image",
        operation_description="Remove an image from a product"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    
    

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['product', 'rating']
    search_fields = ['title', 'comment']
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="List reviews",
        operation_description="Returns a list of approved product reviews. Staff users can see all reviews.",
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
        operation_description="Add a new review for a product. Authentication required.",
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
        operation_summary="Update review",
        operation_description="Update all fields of an existing review"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Partial update review",
        operation_description="Update one or more fields of an existing review"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Reviews"],
        operation_summary="Delete review",
        operation_description="Remove a review from the system"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        # Regular users can see only approved reviews, staff can see all
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="List wishlist items",
        operation_description="Returns a list of products in the user's wishlist. Authentication required."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Add item to wishlist",
        operation_description="Add a product to the user's wishlist. Authentication required.",
        request_body=WishlistSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Retrieve wishlist item",
        operation_description="Get detailed information about a specific wishlist item"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Remove from wishlist",
        operation_description="Remove a product from the user's wishlist"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Update wishlist item",
        operation_description="Update a product in the user's wishlist"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Wishlist"],
        operation_summary="Partial update wishlist item",
        operation_description="Update partial information of a product in user's wishlist"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)