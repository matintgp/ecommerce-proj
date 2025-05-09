from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserAddress

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'is_default') 
    list_filter = ('city',) 
    search_fields = ('user__email', 'address', 'city')

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserAddress, UserAddressAdmin)