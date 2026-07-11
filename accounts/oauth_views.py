from google.auth.transport import requests
import logging
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import CustomUser
from .oauth_services import OAuthService
from .oauth_serializers import GoogleLoginSerializer
from .serializers import UserSerializer
from .views import get_tokens_for_user

logger = logging.getLogger(__name__)

class GoogleOAuthLoginView(APIView):
    """
    POST /api/auth/google/
    Receives Google ID Token, validates it, and logs in or creates a new CustomUser account.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Google OAuth Login",
        request=GoogleLoginSerializer,
        responses={
            200: OpenApiResponse(description="Successful authentication returning tokens and user details."),
            400: OpenApiResponse(description="Invalid Token or parsing exception.")
        }
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data.get('token')

        try:
            profile = OAuthService.verify_google_token(token)
            email = profile['email']
            first_name = profile['first_name']
            last_name = profile['last_name']
            picture_url = profile['profile_picture_url']

            # Find or register CustomUser
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'provider': 'google',
                    'is_verified': True,
                    'role': 'Developer'
                }
            )

            # Update provider if it was local/unset
            if not created and (user.provider == 'local' or not user.provider):
                user.provider = 'google'
                user.is_verified = True
                user.save()

            # Save avatar if newly created or missing image
            if picture_url and (created or not user.profile_picture):
                OAuthService.save_user_avatar(user, picture_url)

            # Generate tokens
            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data

            return Response({
                "success": True,
                "message": "Google Authentication Successful.",
                "data": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh'],
                    "user": user_data
                }
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Google login flow exception: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred during Google authentication."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LinkedInOAuthLoginView(APIView):
    """
    GET /api/auth/linkedin/login/
    Redirects user to the official LinkedIn OAuth authorization consent screen.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="LinkedIn OAuth Redirect",
        responses={302: OpenApiResponse(description="Redirects user to LinkedIn.")}
    )
    def get(self, request):
        try:
            redirect_origin = request.GET.get('redirect_origin')
            auth_url = OAuthService.get_linkedin_login_url(request, redirect_origin=redirect_origin)
            return redirect(auth_url)
        except ValueError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"LinkedIn login redirect exception: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred building LinkedIn redirect URL."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LinkedInOAuthCallbackView(APIView):
    """
    GET /api/auth/linkedin/callback/
    Receives code from LinkedIn, exchanges it for profile info, and redirects back to React with JWT.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="LinkedIn OAuth Callback Handler",
        responses={302: OpenApiResponse(description="Redirects user back to frontend dashboard/login with tokens.")}
    )
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')
        
        # Parse dynamic redirect origin from state
        redirect_origin = None
        if state:
            try:
                import json
                import urllib.parse
                parsed_state = json.loads(urllib.parse.unquote(state))
                if isinstance(parsed_state, dict):
                    redirect_origin = parsed_state.get('redirect_origin')
            except Exception:
                pass
                
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        
        # Validate dynamic redirect_origin before using it
        if redirect_origin:
            import urllib.parse
            is_valid = False
            parsed_origin = urllib.parse.urlparse(redirect_origin)
            origin_domain = parsed_origin.netloc.lower()
            
            # Allow configured CORS origins, local development, and Vercel domains
            if redirect_origin in getattr(settings, 'CORS_ALLOWED_ORIGINS', []):
                is_valid = True
            elif origin_domain == 'localhost' or origin_domain.startswith('localhost:') or origin_domain == '127.0.0.1' or origin_domain.startswith('127.0.0.1:'):
                is_valid = True
            elif origin_domain.endswith('.vercel.app'):
                is_valid = True
                
            if is_valid:
                frontend_url = redirect_origin
                
        # Ensure url does not end with slash to prevent routing bugs
        if frontend_url.endswith('/'):
            frontend_url = frontend_url[:-1]

        if error or not code:
            error_msg = request.GET.get('error_description', 'OAuth flow cancelled.')
            logger.warning(f"LinkedIn OAuth error callback: {error_msg}")
            return redirect(f"{frontend_url}/login?error={requests.utils.quote(error_msg)}")

        try:
            profile = OAuthService.exchange_linkedin_code_for_profile(code, request)
            email = profile['email']
            first_name = profile['first_name']
            last_name = profile['last_name']
            picture_url = profile['profile_picture_url']

            # Find or register CustomUser
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'provider': 'linkedin',
                    'is_verified': True,
                    'role': 'Developer'
                }
            )

            # Update provider if it was local/unset
            if not created and (user.provider == 'local' or not user.provider):
                user.provider = 'linkedin'
                user.is_verified = True
                user.save()

            # Save avatar if newly created or missing image
            if picture_url and (created or not user.profile_picture):
                OAuthService.save_user_avatar(user, picture_url)

            # Generate tokens
            tokens = get_tokens_for_user(user)

            # Redirect back to frontend login with tokens so the client stores them
            redirect_target = f"{frontend_url}/login?access={tokens['access']}&refresh={tokens['refresh']}"
            return redirect(redirect_target)

        except ValueError as e:
            logger.error(f"LinkedIn OAuth processing validation error: {str(e)}")
            return redirect(f"{frontend_url}/login?error={requests.utils.quote(str(e))}")
        except Exception as e:
            logger.error(f"LinkedIn OAuth processing general error: {str(e)}")
            return redirect(f"{frontend_url}/login?error=LinkedIn+processing+failure")
