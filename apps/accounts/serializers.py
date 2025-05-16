from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'created_at', 'updated_at', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
        
    def update(self, instance, validated_data):
        # جلوگیری از تغییر پسورد با متد عادی update
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }
    
    def update(self, instance, validated_data):
        # جلوگیری از تغییر پسورد با متد عادی update
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user   

 


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True, help_text="Refresh token")


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)



class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'otp_code']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp_code')
        
        # بررسی معتبر بودن کد OTP
        try:
            print("Checking OTP validity...")
            print(f"Email: {email}, OTP Code: {otp_code}")
            otp = EmailOTP.objects.filter(
                email=email,
                otp_code=otp_code
            ).latest('created_at')
            
            print(otp)
            
            if not otp.is_valid():
                raise serializers.ValidationError({"otp_code": "کد OTP منقضی شده است."})
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "کد OTP نامعتبر است."})
        
        return data

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'address', 'city', 'postal_code', 'country', 
                 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']