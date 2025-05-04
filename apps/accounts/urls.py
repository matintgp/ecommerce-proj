from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserAddressViewSet

router = DefaultRouter(trailing_slash=True)  # برای افزودن / در انتهای URL
router.register('users', UserViewSet, basename='user')  # تغییر مسیر URL
router.register('addresses', UserAddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]