import logging
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import CustomUser

logger = logging.getLogger(__name__)

class OAuthService:
    @staticmethod
    def verify_google_token(token: str) -> dict:
        """
        Verifies the Google ID Token and extracts user profile data.
        """
        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            raise ValueError("Google Client ID settings is not configured.")
        
        try:
            # Verify the ID Token with Google APIs
            id_info = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                client_id
            )
            
            # Verify audience
            if id_info['aud'] != client_id:
                raise ValueError("Could not verify Google Token audience.")
                
            return {
                "email": id_info.get("email", "").lower().strip(),
                "first_name": id_info.get("given_name", ""),
                "last_name": id_info.get("family_name", "."),
                "profile_picture_url": id_info.get("picture", "")
            }
        except Exception as e:
            logger.error(f"Google token verification failed: {str(e)}")
            raise ValueError(f"Invalid Google credentials: {str(e)}")

    @staticmethod
    def get_linkedin_login_url(request) -> str:
        """
        Constructs the authorization URL to redirect users to LinkedIn login.
        """
        client_id = settings.LINKEDIN_CLIENT_ID
        if not client_id:
            raise ValueError("LinkedIn Client ID settings is not configured.")
        
        redirect_uri = request.build_absolute_uri(reverse('auth_linkedin_callback'))
        
        # OpenID connect params
        scope = "openid profile email"
        state = "linkedin_oauth_state"
        
        url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri={requests.utils.quote(redirect_uri)}&"
            f"scope={requests.utils.quote(scope)}&"
            f"state={state}"
        )
        return url

    @staticmethod
    def exchange_linkedin_code_for_profile(code: str, request) -> dict:
        """
        Exchanges LinkedIn authorization code for profile metrics.
        """
        client_id = settings.LINKEDIN_CLIENT_ID
        client_secret = settings.LINKEDIN_CLIENT_SECRET
        if not client_id or not client_secret:
            raise ValueError("LinkedIn Client credentials are not configured.")
            
        redirect_uri = request.build_absolute_uri(reverse('auth_linkedin_callback'))
        
        # Token exchange endpoint
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        response = requests.post(token_url, data=payload, timeout=10)
        if not response.ok:
            logger.error(f"LinkedIn code exchange failed: {response.text}")
            raise ValueError("Failed to retrieve access token from LinkedIn.")
            
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Fetch user info using OpenID userinfo endpoint
        userinfo_url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
        
        if not userinfo_response.ok:
            logger.error(f"LinkedIn userinfo request failed: {userinfo_response.text}")
            raise ValueError("Failed to retrieve profile data from LinkedIn.")
            
        profile_data = userinfo_response.json()
        
        return {
            "email": profile_data.get("email", "").lower().strip(),
            "first_name": profile_data.get("given_name", ""),
            "last_name": profile_data.get("family_name", "."),
            "profile_picture_url": profile_data.get("picture", "")
        }

    @staticmethod
    def save_user_avatar(user: CustomUser, url: str) -> None:
        """
        Downloads a profile avatar from a URL and saves it to the profile_picture Field.
        """
        if not url:
            return
            
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                file_name = f"social_{user.uuid}_avatar.jpg"
                user.profile_picture.save(file_name, ContentFile(response.content), save=True)
        except Exception as e:
            logger.error(f"Failed to save social avatar picture: {str(e)}")
