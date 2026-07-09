from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .validators import (
    validate_strong_password,
    validate_phone_number,
    validate_date_of_birth,
    validate_linkedin_url,
    validate_github_url,
    validate_profile_picture_file
)

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer to represent a user profile read-only output.
    """
    class Meta:
        model = CustomUser
        fields = [
            'id', 'uuid', 'first_name', 'last_name', 'email', 
            'phone_number', 'country', 'profile_picture', 'bio', 
            'date_of_birth', 'gender', 'linkedin_url', 'github_url', 
            'portfolio_url', 'role', 'is_verified', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates and registers new CustomUser records.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_strong_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'password', 
            'password_confirm', 'phone_number', 'country'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            country=validated_data.get('country', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates email and password parameters for authentication.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials.")
                )
            if not user.is_active:
                raise serializers.ValidationError(_("User account is disabled."))
            attrs['user'] = user
        else:
            raise serializers.ValidationError(_("Must include 'email' and 'password'."))
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Validates fields to allow updating authenticated profile records.
    """
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False, validators=[validate_phone_number])
    date_of_birth = serializers.DateField(required=False, validators=[validate_date_of_birth])
    linkedin_url = serializers.URLField(required=False, validators=[validate_linkedin_url])
    github_url = serializers.URLField(required=False, validators=[validate_github_url])
    profile_picture = serializers.ImageField(required=False, validators=[validate_profile_picture_file])

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'bio', 
            'country', 'date_of_birth', 'gender', 'linkedin_url', 
            'github_url', 'portfolio_url', 'role', 'profile_picture'
        ]

    def update(self, instance, validated_data):
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates change password credentials.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True, 
        validators=[validate_strong_password]
    )
    password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Validates user email request for OTP trigger.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("No active account exists matching this email address.")
            )
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """
    Validates OTP matching code checks.
    """
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": _("No account found matching this email.")})
            
        if user.otp_code != otp:
            raise serializers.ValidationError({"otp": _("Invalid OTP code.")})
            
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """
    Validates reset credentials using matching OTP verification codes.
    """
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(
        required=True, 
        write_only=True, 
        validators=[validate_strong_password]
    )
    password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
            
        user = CustomUser.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError({"email": _("No account found matching this email.")})
            
        if user.otp_code != attrs['otp']:
            raise serializers.ValidationError({"otp": _("Invalid or expired OTP.")})
            
        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    """
    Validates email verification tokens or OTP codes.
    """
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True)


class ResendVerificationSerializer(serializers.Serializer):
    """
    Validates email for resending verification code links.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        user = CustomUser.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError(_("No account exists matching this email address."))
        if user.is_verified:
            raise serializers.ValidationError(_("This email is already verified."))
        return value
