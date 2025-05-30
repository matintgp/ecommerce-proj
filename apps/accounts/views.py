from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, parser_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, logout
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


from .models import User, UserAddress
from .serializers import *



















class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser) 
    filter_backends = [SearchFilter]
    search_fields = ['username']
    http_method_names = ['get', 'post', 'put', 'delete']
    pagination_class = None 
    
    def get_permissions(self): 
        if self.action in ['register', 'login', 'logout_user', "send_verification_email"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    
    @swagger_auto_schema(
        operation_summary="Send email verification code",
        operation_description="Send a verification code to the user's email",
        request_body=EmailVerificationSerializer,
        tags=['Users']
    )
    @action(detail=False, methods=['post'], url_path='send-verification')
    def send_verification_email(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data['email']
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "این ایمیل قبلا ثبت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        EmailOTP.objects.filter(email=email).delete()
        otp = EmailOTP(email=email)
        otp.save()
        
        print(f"[+++]  Generated OTP: {otp.otp_code}  [+++]") # Debug 
        
        subject = 'کد تایید ایمیل'
        message = f'کد تایید شما: {otp.otp_code}\nاین کد تا 10 دقیقه معتبر است.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
            return Response(
                {"message": "کد تایید با موفقیت به ایمیل شما ارسال شد", "email": email},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"خطا در ارسال ایمیل: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Create a new user account with username, email and password",
        request_body=UserRegistrationSerializer,
        tags=['Users']
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        email = serializer.validated_data.get('email')
        otp_code = serializer.validated_data.get('otp_code')
        
        try:
            otp = EmailOTP.objects.filter(
                email=email,
                otp_code=otp_code
            ).latest('created_at')
            
            print(f"OTP Code: {otp}")  # Debug
            
            if timezone.now() > otp.expires_at:
                return Response(
                    {"error": "کد تایید منقضی شده است. لطفا دوباره تلاش کنید."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp.otp_code != otp_code:
                return Response(
                    {"error": "کد تایید نادرست است"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            otp.is_verified = True
            otp.save()
            
            user_data = {
                'username': serializer.validated_data.get('username'),
                'email': email,
                'first_name': serializer.validated_data.get('first_name'),
                'last_name': serializer.validated_data.get('last_name'),
                'password': serializer.validated_data.get('password')
            }
            
            user = User.objects.create_user(**user_data)
            user.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
            
        except EmailOTP.DoesNotExist:
            return Response(
                {"error": "کد تایید نامعتبر است یا قبلا استفاده شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )
            

    @swagger_auto_schema(
        operation_summary="User login",
        operation_description="Login with username and password to get auth tokens",
        request_body=UserLoginSerializer,
        tags=['Users']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        print(f"Username: {username}, Password: {password}")  # Debug
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            user_serializer = self.get_serializer(user)
            return Response({
                'user': user_serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'نام کاربری یا رمز عبور اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)
    
    
    @swagger_auto_schema(
        operation_summary="User logout",
        operation_description="Logout the current user",
        request_body=UserLogoutSerializer,
        tags=['Users']
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout_user(self, request):
        serializer = UserLogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "با موفقیت از سیستم خارج شدید."}, status=status.HTTP_205_RESET_CONTENT)

                            


    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Get the profile of the currently logged in user",
        tags=['Users']
    )
    @action(detail=False, methods=['get'], url_path='profile')
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    
    @swagger_auto_schema(
        method="put",
        operation_summary="Update user profile",
        operation_description="Update the currently logged in user's profile (PUT)",
        request_body=UserUpdateSerializer,
        tags=['Users']
    )
    @swagger_auto_schema(
        method="patch",
        operation_summary="Partial update user profile",
        operation_description="Update part of the currently logged in user's profile (PATCH)",
        request_body=UserUpdateSerializer,
        tags=['Users']
    )
    @action(detail=False, methods=['put', 'patch'], url_path='profile/update')
    def update_profile(self, request):
        user = request.user
        
        serializer = UserUpdateSerializer(
            user, 
            data=request.data, 
            partial=request.method == "PATCH"
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    


class UserAddressViewSet(viewsets.GenericViewSet):  
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Get all addresses",
        operation_description="Get all addresses for the current user",
        tags=['User Addresses']
    )
    @action(detail=False, methods=['get'], url_path='')
    def list_addresses(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add new address",
        operation_description="Add a new address for the current user",
        tags=['User Addresses']
    )
    @action(detail=False, methods=['post'], url_path='')
    def add_address(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method="put",
        operation_summary="Update address",
        operation_description="Update an existing address (PUT)",
        tags=['User Addresses']
    )
    @swagger_auto_schema(
        method="patch",
        operation_summary="Partial update address",
        operation_description="Update part of an existing address (PATCH)",
        tags=['User Addresses']
    )
    @action(detail=True, methods=['put', 'patch'], url_path='')
    def update_address(self, request, pk=None):
        address = get_object_or_404(UserAddress, id=pk, user=request.user)
        serializer = self.get_serializer(address, data=request.data, partial=request.method == "PATCH")
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Delete address",
        operation_description="Delete an address by ID",
        tags=['User Addresses']
    )
    @action(detail=True, methods=['delete'], url_path='')
    def delete_address(self, request, pk=None):
        address = get_object_or_404(UserAddress, id=pk, user=request.user)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)