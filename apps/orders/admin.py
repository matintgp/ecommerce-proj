# from django.contrib import admin
# from .models import Order, OrderItem

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     raw_id_fields = ['product']
#     extra = 0

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['user__email', 'id']
#     inlines = [OrderItemInline]
#     list_per_page = 25