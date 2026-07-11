import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware that intercepts requests to /api/admin/ (except login and refresh token)
    and verifies that the token carries the `is_admin_token` claim, and that the
    user has `is_staff = True`.
    """
    def process_request(self, request):
        # Protect paths starting with /api/admin/ (except login and token refresh)
        if (request.path.startswith('/api/admin/') or request.path.startswith('/api/admin')) and \
           not request.path.startswith('/api/admin/login') and \
           not request.path.startswith('/api/admin/token/refresh'):
            
            auth_header = request.headers.get('Authorization', '')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'success': False,
                    'message': 'Authentication credentials were not provided.'
                }, status=401)
            
            try:
                parts = auth_header.split(' ')
                if len(parts) != 2:
                    raise Exception("Malformed authorization header.")
                
                token_str = parts[1]
                # Decode the access token using SimpleJWT
                token = AccessToken(token_str)
                
                # Verify the custom claim
                if not token.get('is_admin_token'):
                    return JsonResponse({
                        'success': False,
                        'message': 'Access denied: Token is not an admin session token.'
                    }, status=403)
                
                # Fetch user from token claim
                user_id = token.get('user_id')
                user = User.objects.get(id=user_id)
                
                if not user.is_staff:
                    return JsonResponse({
                        'success': False,
                        'message': 'Access denied: User does not have staff permissions.'
                    }, status=403)
                
                # Attach authenticated user to request
                request.user = user
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid or expired token: {str(e)}'
                }, status=401)
