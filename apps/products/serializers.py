from rest_framework import serializers
from django.db.models import Avg
from .models import *



class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'slug', 'color_code']
        read_only_fields = ['id', 'slug']

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['id', 'name', 'value']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_feature']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']
        read_only_fields = ['id', 'slug']

class ReviewSerializer(serializers.ModelSerializer): # این سریالایزر برای نمایش نظرات لازم است
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user_email', 'rating', 'title', 'comment', 'created_at', 'is_approved']
        read_only_fields = ['id', 'created_at', 'is_approved']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    
    brand = BrandSerializer(read_only=True)
    gender = GenderSerializer(read_only=True)
    sizes = SizeSerializer(many=True, read_only=True, source='size')
    colors = ColorSerializer(many=True, read_only=True, source='color') # اطمینان از اینکه source='color' صحیح است
    specifications = SpecificationSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    reviews = ReviewSerializer(many=True, read_only=True, source='reviews.all') 
    average_rating = serializers.SerializerMethodField()
    is_in_wishlist = serializers.SerializerMethodField()

    def get_average_rating(self, obj):
        avg_rating = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 2) if avg_rating else None

    def get_is_in_wishlist(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        try:
            data['price'] = int(float(data['price']))
            data['price_with_commas'] = "{:,.0f}".format(data['price'])
        except (ValueError, TypeError):
            pass
        
        # فیلتر کردن نظرات برای نمایش فقط نظرات تایید شده
        approved_reviews = instance.reviews.filter(is_approved=True)
        # اطمینان از اینکه context به ReviewSerializer پاس داده می‌شود اگر نیاز به request در آنجا هم باشد
        data['reviews'] = ReviewSerializer(approved_reviews, many=True, context=self.context).data
        
        return data

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock', 'is_active', 
            'category', 'category_id', 'brand', 'gender', 'sizes', 'colors', 
            'specifications', 'images', 'created_at', 'updated_at',
            'reviews', 'average_rating', 'is_in_wishlist' # اضافه کردن فیلدهای جدید به اینجا
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 
            'reviews', 'average_rating', 'is_in_wishlist' # اضافه کردن فیلدهای جدید به اینجا نیز
        ]
        


class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_details', 'added_at']

        