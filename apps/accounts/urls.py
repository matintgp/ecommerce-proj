from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserAddressViewSet

router = DefaultRouter()   
router.register('users', UserViewSet, basename='user')   
router.register('addresses', UserAddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]