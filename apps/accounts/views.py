from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, parser_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, logout
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, UserAddress
from .serializers import UserSerializer, UserAddressSerializer


class UserViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser)  # برای پشتیبانی از آپلود فایل
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']
    swagger_schema_fields = {
        "tags": ["Users"]
    }
    
    def get_permissions(self):
        # تنظیم دسترسی اندپوینت‌ها
        if self.action in ['register', 'login', 'get_by_username', 'get_by_email']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Create a new user account with username, email and password"
    )
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """ثبت‌نام کاربر جدید"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="User login",
        operation_description="Login with username and password to get auth tokens"
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """ورود کاربر به سیستم"""
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            serializer = self.get_serializer(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'نام کاربری یا رمز عبور اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)
    
    @swagger_auto_schema(
        operation_summary="User logout",
        operation_description="Logout the current user"
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout_user(self, request):
        """خروج کاربر از سیستم"""
        logout(request)
        return Response({"message": "با موفقیت از سیستم خارج شدید."}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Get the profile of the currently logged in user"
    )
    @action(detail=False, methods=['get'], url_path='profile')
    def profile(self, request):
        """دریافت پروفایل کاربر"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    # تغییر این قسمت برای رفع خطا - متدها را جدا کنید
    @swagger_auto_schema(
        method="put",
        operation_summary="Update user profile",
        operation_description="Update the profile of the currently logged in user (PUT)"
    )
    @swagger_auto_schema(
        method="patch",
        operation_summary="Partial update user profile",
        operation_description="Update part of the profile of the currently logged in user (PATCH)"
    )
    @action(detail=False, methods=['put', 'patch'], url_path='profile')
    def update_profile(self, request):
        """بروزرسانی پروفایل کاربر"""
        serializer = self.get_serializer(request.user, data=request.data, partial=request.method == "PATCH")
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Get user by ID",
        operation_description="Get detailed information about a user by their ID"
    )
    @action(detail=True, methods=['get'], url_path='')
    def get_by_id(self, request, pk=None):
        """دریافت کاربر براساس شناسه"""
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Delete user by ID",
        operation_description="Delete a user account by ID"
    )
    @action(detail=True, methods=['delete'], url_path='')
    def delete_user(self, request, pk=None):
        """حذف کاربر براساس شناسه"""
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    @swagger_auto_schema(
        method="put",
        operation_summary="Update user by ID",
        operation_description="Update an existing user by ID (PUT)"
    )
    @swagger_auto_schema(
        method="patch",
        operation_summary="Partial update user by ID",
        operation_description="Update part of an existing user by ID (PATCH)"
    )
    @action(detail=True, methods=['put', 'patch'], url_path='')
    def update_user(self, request, pk=None):
        """بروزرسانی کاربر با شناسه مشخص"""
        user = self.get_object()
        
        # بررسی دسترسی - فقط خود کاربر یا ادمین می‌تواند ویرایش کند
        if not (request.user.is_staff or request.user.id == user.id):
            return Response(
                {"error": "شما دسترسی لازم برای ویرایش این کاربر را ندارید."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(
            user, 
            data=request.data, 
            partial=request.method == "PATCH"
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @swagger_auto_schema(
        operation_summary="Get user by username",
        operation_description="Find a user by their username",
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_PATH, description="Username to search for", type=openapi.TYPE_STRING),
        ]
    )
    @action(detail=False, methods=['get'], url_path='username/(?P<username>[^/.]+)')
    def get_by_username(self, request, username=None):
        """دریافت کاربر براساس نام کاربری"""
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Get user by email",
        operation_description="Find a user by their email address",
        manual_parameters=[
            openapi.Parameter('email', openapi.IN_PATH, description="Email to search for", type=openapi.TYPE_STRING),
        ]
    )
    @action(detail=False, methods=['get'], url_path='email/(?P<email>[^/.]+)')
    def get_by_email(self, request, email=None):
        """دریافت کاربر براساس ایمیل"""
        user = get_object_or_404(User, email=email)
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class UserAddressViewSet(viewsets.GenericViewSet):
    """
    API endpoints for managing user addresses
    """
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    swagger_schema_fields = {
        "tags": ["Addresses"]
    }

    def get_queryset(self):
        # Avoid error when generating Swagger docs
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Get all addresses",
        operation_description="Get all addresses for the current user"
    )
    @action(detail=False, methods=['get'], url_path='')
    def list_addresses(self, request):
        """دریافت تمام آدرس‌های کاربر"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add new address",
        operation_description="Add a new address for the current user"
    )
    @action(detail=False, methods=['post'], url_path='')
    def add_address(self, request):
        """افزودن آدرس جدید"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # تغییر این قسمت برای رفع خطا - متدها را جدا کنید
    @swagger_auto_schema(
        method="put",
        operation_summary="Update address",
        operation_description="Update an existing address (PUT)"
    )
    @swagger_auto_schema(
        method="patch",
        operation_summary="Partial update address",
        operation_description="Update part of an existing address (PATCH)"
    )
    @action(detail=True, methods=['put', 'patch'], url_path='')
    def update_address(self, request, pk=None):
        """بروزرسانی آدرس"""
        address = get_object_or_404(UserAddress, id=pk, user=request.user)
        serializer = self.get_serializer(address, data=request.data, partial=request.method == "PATCH")
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Delete address",
        operation_description="Delete an address by ID"
    )
    @action(detail=True, methods=['delete'], url_path='')
    def delete_address(self, request, pk=None):
        """حذف آدرس"""
        address = get_object_or_404(UserAddress, id=pk, user=request.user)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)