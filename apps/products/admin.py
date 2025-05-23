from django.contrib import admin
from .models import *
from django.contrib.auth.models import Group


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty forms to display


class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 1



@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}



# @admin.register(Specification)
# class SpecificationAdmin(admin.ModelAdmin):
#     list_display = ('product', 'name', 'value')
#     list_filter = ('product',)
#     search_fields = ('product__name', 'name')
#     ordering = ('product',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)} 
    ordering = ('-created_at',)
    inlines = [ProductImageInline, SpecificationInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'comment')
    list_editable = ('is_approved',)


admin.site.unregister(Group)