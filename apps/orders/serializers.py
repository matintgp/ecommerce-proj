from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'quantity', 'status']
        read_only_fields = ['id', 'user']  # Assuming user is set automatically on creation
