from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils import timezone

from .models import CustomUser
from .permissions import IsSelf
from .services import AuthService
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer
)

def get_tokens_for_user(user) -> dict:
    """
    Generates SimpleJWT access and refresh tokens for a user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    """
    POST /api/auth/register
    Registers a new CustomUser and triggers a verification email code.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register New Account",
        description="Creates a new developer profile and sends a 6-digit verification code email.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="User successfully registered."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate & send verification OTP
        otp = AuthService.set_user_otp(user)
        AuthService.send_verification_email(user, otp)

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data
        
        return Response({
            "success": True,
            "message": "User registered successfully. Please verify your email with the sent OTP.",
            "data": {
                "user": user_data,
                "tokens": tokens
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login
    Authenticates a user via email and password, returning tokens and profile.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="User Login",
        description="Authenticates credentials and returns SimpleJWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful."),
            400: OpenApiResponse(description="Invalid credentials.")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Simple login signal trigger
        login(request, user)
        
        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            "success": True,
            "message": "Login Successful",
            "data": {
                "user": user_data,
                "tokens": tokens
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout
    Blacklists the active SimpleJWT refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout User",
        description="Blacklists the provided refresh token to terminate session.",
        responses={
            200: OpenApiResponse(description="Logout successful."),
            400: OpenApiResponse(description="Invalid refresh token.")
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": "Refresh token is required.",
                    "errors": {"refresh": ["This field is required."]}
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "success": True,
                "message": "Logout successful.",
                "data": {}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Invalid or blacklisted token.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """
    GET /api/auth/me
    Returns the currently authenticated user's complete profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Current User Profile",
        description="Returns detailed profile parameters of the authenticated requester.",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            "success": True,
            "message": "Profile fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    """
    PUT /api/auth/profile
    Updates profile fields for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Update Profile Details",
        description="Updates authenticated fields including name, bio, social URLs, and avatar picture files.",
        request=UpdateProfileSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_data = UserSerializer(user).data
        return Response({
            "success": True,
            "message": "Profile updated successfully.",
            "data": user_data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password
    Modifies security passwords for authenticated users.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Change Password",
        description="Validates old password and sets new validated passwords.",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password modified successfully."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                "success": False,
                "message": "Invalid credentials",
                "errors": {"old_password": ["Current password is incorrect."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            "success": True,
            "message": "Password changed successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password
    Triggers code generators and emails OTP security codes.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Forgot Password OTP Trigger",
        description="Verifies email existence, updates user OTP registers, and emails security codes.",
        request=ForgotPasswordSerializer,
        responses={200: OpenApiResponse(description="OTP successfully emailed.")}
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        otp = AuthService.set_user_otp(user)
        AuthService.send_password_reset_email(user, otp)
        
        return Response({
            "success": True,
            "message": "Password reset OTP code sent successfully to email.",
            "data": {}
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp
    Checks if email-OTP credentials match and are active.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Verify Recovery OTP",
        description="Checks if OTP code matches the active database registries.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP code valid."),
            400: OpenApiResponse(description="Invalid code or expired timing.")
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        user = CustomUser.objects.get(email=email)
        
        is_valid = AuthService.verify_user_otp(user, otp)
        if not is_valid:
            # Put back the OTP if verification failed (optional, or fail directly)
            user.otp_code = otp
            user.save()
            return Response({
                "success": False,
                "message": "Verification Error",
                "errors": {"otp": ["OTP has expired or is invalid."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Re-set verification status temporarily so password can be reset
        user.otp_code = 'VALID'
        user.otp_created_at = timezone.now()
        user.save()

        return Response({
            "success": True,
            "message": "OTP verification successful.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password
    Resets account password using OTP validation tokens.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Reset Security Password",
        description="Resets account password once matching OTP keys are verified.",
        request=ResetPasswordSerializer,
        responses={200: OpenApiResponse(description="Password reset successful.")}
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        user.set_password(serializer.validated_data['new_password'])
        user.otp_code = ''
        user.otp_created_at = None
        user.save()
        
        return Response({
            "success": True,
            "message": "Password has been reset successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email
    Flags is_verified status to True when correct codes match.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Verify Email Address",
        description="Validates OTP verification code to confirm user email authenticity.",
        request=VerifyEmailSerializer,
        responses={200: OpenApiResponse(description="Email verified successfully.")}
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        user = CustomUser.objects.get(email=email)
        
        is_valid = AuthService.verify_user_otp(user, token)
        if not is_valid:
            return Response({
                "success": False,
                "message": "Verification Error",
                "errors": {"token": ["Token has expired or is invalid."]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user.is_verified = True
        user.save()
        
        return Response({
            "success": True,
            "message": "Email verified successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ResendVerificationView(APIView):
    """
    POST /api/auth/resend-verification
    Regenerates and dispatches new validation link alerts.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Resend Verification OTP",
        description="Triggers creation of fresh verification OTPs and dispatches email instructions.",
        request=ResendVerificationSerializer,
        responses={200: OpenApiResponse(description="Verification code sent.")}
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        otp = AuthService.set_user_otp(user)
        AuthService.send_verification_email(user, otp)
        
        return Response({
            "success": True,
            "message": "Verification email resent successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom SimpleJWT refresh view returning success/error wrapper format.
    """
    @extend_schema(
        summary="Refresh Access Token",
        description="Validates SimpleJWT refresh token and generates fresh access token keys.",
        responses={200: OpenApiResponse(description="Token refreshed.")}
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                "success": True,
                "message": "Token refreshed successfully.",
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Token refresh error",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
