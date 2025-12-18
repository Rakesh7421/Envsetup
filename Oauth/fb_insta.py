#!/usr/bin/env python3
"""
Facebook/Instagram OAuth Template Script
This script demonstrates how to load OAuth credentials from a .env file
and provides a basic structure for OAuth operations using Facebook Business login.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()

class OAuthHandler:
    """
    A class to handle Facebook/Instagram OAuth operations using environment variables.
    Uses Facebook Business login method for Instagram authentication.
    """

    def __init__(self):
        """
        Initialize the OAuth handler by loading credentials from environment variables.
        """
        self.client_id = os.getenv('FB_CLIENT_ID')
        self.client_secret = os.getenv('FB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('FB_REDIRECT_URI')
        self.instagram_redirect_uri = os.getenv('INSTA_REDIRECT_URI', self.redirect_uri)

        # Validate that required credentials are present
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """
        Validate that required OAuth credentials are present in environment variables.
        Raises an exception if any required credential is missing.
        """
        required_vars = {
            'Facebook': ['FB_CLIENT_ID', 'FB_CLIENT_SECRET', 'FB_REDIRECT_URI']
        }

        missing_vars = []

        for platform, vars_list in required_vars.items():
            for var in vars_list:
                if not os.getenv(var):
                    missing_vars.append(f"{platform} {var}")

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please ensure these are set in your .env file."
            )

    def get_auth_url(self, platform: str = 'facebook') -> str:
        """
        Generate the OAuth authorization URL for the specified platform.

        Args:
            platform: Either 'facebook' or 'instagram'

        Returns:
            The authorization URL as a string

        Raises:
            ValueError: If an invalid platform is specified
        """
        if platform.lower() == 'facebook':
            base_url = "https://www.facebook.com/v12.0/dialog/oauth"
            client_id = self.client_id
            redirect_uri = self.redirect_uri
            scope = "email,public_profile"
        elif platform.lower() == 'instagram':
            # Instagram uses Facebook Business login method
            base_url = "https://www.facebook.com/v12.0/dialog/oauth"
            client_id = self.client_id
            redirect_uri = self.instagram_redirect_uri
            scope = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
        else:
            raise ValueError(f"Unsupported platform: {platform}. Use 'facebook' or 'instagram'")

        return f"{base_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code"

    def exchange_code_for_token(self, code: str, platform: str = 'facebook') -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token.

        Args:
            code: The authorization code received from the OAuth redirect
            platform: Either 'facebook' or 'instagram'

        Returns:
            Dictionary containing the access token and other response data

        Raises:
            ValueError: If an invalid platform is specified
            requests.exceptions.RequestException: If the token exchange fails
        """
        if platform.lower() == 'facebook':
            token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
            client_id = self.client_id
            client_secret = self.client_secret
            redirect_uri = self.redirect_uri
        elif platform.lower() == 'instagram':
            # Instagram uses Facebook's token endpoint
            token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
            client_id = self.client_id
            client_secret = self.client_secret
            redirect_uri = self.instagram_redirect_uri
        else:
            raise ValueError(f"Unsupported platform: {platform}. Use 'facebook' or 'instagram'")

        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }

        try:
            response = requests.get(token_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to exchange code for token: {str(e)}"
            ) from e

    def get_user_info(self, access_token: str, platform: str = 'facebook') -> Dict[str, Any]:
        """
        Get user information using an access token.

        Args:
            access_token: The OAuth access token
            platform: Either 'facebook' or 'instagram'

        Returns:
            Dictionary containing user information

        Raises:
            ValueError: If an invalid platform is specified
            requests.exceptions.RequestException: If the API request fails
        """
        if platform.lower() == 'facebook':
            api_url = f"https://graph.facebook.com/me?access_token={access_token}&fields=id,name,email"
        elif platform.lower() == 'instagram':
            # For Instagram, we need to get the Instagram Business Account ID first
            # This requires the user to have connected their Instagram account to a Facebook Page
            api_url = f"https://graph.facebook.com/me/accounts?access_token={access_token}&fields=instagram_business_account"
        else:
            raise ValueError(f"Unsupported platform: {platform}. Use 'facebook' or 'instagram'")

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get user info: {str(e)}"
            ) from e

    def get_instagram_user_info(self, access_token: str, instagram_business_account_id: str) -> Dict[str, Any]:
        """
        Get Instagram user information using an access token and Instagram Business Account ID.

        Args:
            access_token: The OAuth access token
            instagram_business_account_id: The Instagram Business Account ID

        Returns:
            Dictionary containing Instagram user information

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        api_url = f"https://graph.facebook.com/{instagram_business_account_id}?access_token={access_token}&fields=id,username,biography,followers_count,media_count"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get Instagram user info: {str(e)}"
            ) from e

def main():
    """
    Main function demonstrating basic OAuth workflow using Facebook Business login.
    """
    try:
        # Initialize OAuth handler
        oauth = OAuthHandler()

        print("Facebook/Instagram OAuth Template (Facebook Business Login)")
        print("=" * 60)

        # Example: Generate Facebook auth URL
        fb_auth_url = oauth.get_auth_url('facebook')
        print(f"Facebook Auth URL: {fb_auth_url}")

        # Example: Generate Instagram auth URL (uses Facebook Business login)
        insta_auth_url = oauth.get_auth_url('instagram')
        print(f"Instagram Auth URL (Facebook Business): {insta_auth_url}")

        print("\nTo complete the OAuth flow:")
        print("1. Visit the auth URL in your browser")
        print("2. Authorize the application")
        print("3. You'll be redirected with a 'code' parameter")
        print("4. Use that code with exchange_code_for_token() method")
        print("5. For Instagram: First get user accounts, then use get_instagram_user_info()")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure you have a .env file with the required credentials:")
        print("FB_CLIENT_ID=your_facebook_client_id")
        print("FB_CLIENT_SECRET=your_facebook_client_secret")
        print("FB_REDIRECT_URI=your_facebook_redirect_uri")
        print("INSTA_REDIRECT_URI=your_instagram_redirect_uri (optional, defaults to FB_REDIRECT_URI)")

if __name__ == "__main__":
    main()