from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CurrentUserView,
    UpdateProfileView,
    ChangePasswordView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    VerifyEmailView,
    ResendVerificationView,
    CustomTokenRefreshView
)
from .oauth_views import (
    GoogleOAuthLoginView,
    LinkedInOAuthLoginView,
    LinkedInOAuthCallbackView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='auth_register'),
    path('login', LoginView.as_view(), name='auth_login'),
    path('logout', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('google/', GoogleOAuthLoginView.as_view(), name='auth_google_login'),
    path('linkedin/login/', LinkedInOAuthLoginView.as_view(), name='auth_linkedin_login'),
    path('linkedin/callback/', LinkedInOAuthCallbackView.as_view(), name='auth_linkedin_callback'),
    
    path('me', CurrentUserView.as_view(), name='auth_me'),
    path('profile', UpdateProfileView.as_view(), name='auth_profile_update'),
    path('change-password', ChangePasswordView.as_view(), name='auth_change_password'),
    
    path('forgot-password', ForgotPasswordView.as_view(), name='auth_forgot_password'),
    path('verify-otp', VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('reset-password', ResetPasswordView.as_view(), name='auth_reset_password'),
    
    path('verify-email', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('resend-verification', ResendVerificationView.as_view(), name='auth_resend_verification'),
]
