from django.contrib import admin
from .models import Product, Category, ProductImage, Review, Wishlist

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty forms to display

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)} 
    ordering = ('-created_at',)
    inlines = [ProductImageInline]  # This enables adding images directly in the product admin form

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_feature')
    list_filter = ('is_feature', 'created_at')
    search_fields = ('product__name', 'alt_text')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'comment')
    list_editable = ('is_approved',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__email', 'product__name')