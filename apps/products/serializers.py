from rest_framework import serializers
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

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    
    brand = BrandSerializer(read_only=True)
    gender = GenderSerializer(read_only=True)
    sizes = SizeSerializer(many=True, read_only=True, source='size')
    colors = ColorSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        try:
            data['price'] = int(float(data['price']))
            data['price_with_commas'] = "{:,.0f}".format(data['price'])
        except (ValueError, TypeError):
            pass
        return data

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'stock', 'is_active', 
                  'category', 'category_id', 'brand', 'gender', 'sizes', 'colors', 'specifications',
                  'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'user_email', 'rating', 
                 'title', 'comment', 'created_at', 'is_approved']
        extra_kwargs = {'user': {'write_only': True}}

class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_details', 'added_at']

        