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

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'product', 'user_email', 'rating', 'title', 'comment', 'created_at', 'is_approved']  
        read_only_fields = ['id', 'user_email', 'created_at', 'is_approved']

    def validate(self, data):
        user = self.context['request'].user
        product = data['product']
        
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("شما قبلاً برای این محصول نظر داده‌اید.")
        return data
    
    def create(self, validated_data):
        validated_data['is_approved'] = True
        return super().create(validated_data)
    
    
    
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    
    brand = BrandSerializer(read_only=True)
    gender = GenderSerializer(read_only=True)
    sizes = SizeSerializer(many=True, read_only=True, source='size')
    colors = ColorSerializer(many=True, read_only=True, source='color') 
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
        
        approved_reviews = instance.reviews.filter(is_approved=True)
        data['reviews'] = ReviewSerializer(approved_reviews, many=True, context=self.context).data
        
        return data

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock', 'is_active', 
            'category', 'category_id', 'brand', 'gender', 'sizes', 'colors', 
            'specifications', 'images', 'created_at', 'updated_at',
            'reviews', 'average_rating', 'is_in_wishlist' 
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 
            'reviews', 'average_rating', 'is_in_wishlist' 
        ]
        


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['product']
    
    def validate(self, data):
        user = self.context['request'].user
        product = data['product']
        
        if Wishlist.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("این محصول قبلاً در لیست علاقه‌مندی‌های شما موجود است.")
        
        return data

class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_details', 'added_at']
        read_only_fields = ['added_at']