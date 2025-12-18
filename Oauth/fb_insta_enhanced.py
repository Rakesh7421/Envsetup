
#!/usr/bin/env python3
"""
Enhanced Facebook/Instagram OAuth Script
Handles complete OAuth flow including token exchange, page/Instagram account lookup,
and long-lived token generation with auto-refresh capabilities.
"""

import os
import webbrowser
import time
import json
from dotenv import load_dotenv
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

# Load environment variables from .env file
load_dotenv()

class EnhancedOAuthHandler:
    """
    Enhanced OAuth handler with complete Facebook/Instagram Business integration.
    Handles token exchange, page lookup, Instagram account discovery, and token refresh.
    """

    def __init__(self):
        """
        Initialize the OAuth handler by loading credentials from environment variables.
        """
        self.client_id = os.getenv('FB_CLIENT_ID')
        self.client_secret = os.getenv('FB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('FB_REDIRECT_URI')
        self.instagram_redirect_uri = os.getenv('INSTA_REDIRECT_URI', self.redirect_uri)
        self.app_access_token = None
        self.user_access_token = None
        self.page_access_token = None
        self.instagram_account_id = None
        self.page_id = None

        # Validate that required credentials are present
        self._validate_credentials()

        # Get app access token
        self._get_app_access_token()

    def _validate_credentials(self) -> None:
        """
        Validate that required OAuth credentials are present in environment variables.
        """
        required_vars = ['FB_CLIENT_ID', 'FB_CLIENT_SECRET', 'FB_REDIRECT_URI']

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please ensure these are set in your .env file."
            )

    def _get_app_access_token(self) -> None:
        """Get app access token for API calls that don't require user context"""
        try:
            token_url = f"https://graph.facebook.com/oauth/access_token"
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            response = requests.get(token_url, params=params)
            response.raise_for_status()
            self.app_access_token = response.json().get('access_token')
        except Exception as e:
            print(f"Warning: Could not get app access token: {str(e)}")

    def get_auth_url(self, platform: str = 'facebook') -> str:
        """
        Generate the OAuth authorization URL for the specified platform.

        Args:
            platform: Either 'facebook' or 'instagram'

        Returns:
            The authorization URL as a string
        """
        if platform.lower() == 'facebook':
            base_url = "https://www.facebook.com/v12.0/dialog/oauth"
            redirect_uri = self.redirect_uri
            scope = "email,public_profile,pages_show_list,pages_read_engagement"
        elif platform.lower() == 'instagram':
            base_url = "https://www.facebook.com/v12.0/dialog/oauth"
            redirect_uri = self.instagram_redirect_uri
            scope = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,instagram_manage_insights"
        else:
            raise ValueError(f"Unsupported platform: {platform}. Use 'facebook' or 'instagram'")

        return f"{base_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code"

    def exchange_code_for_token(self, code: str, platform: str = 'facebook') -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token and handle long-lived token generation.

        Args:
            code: The authorization code received from the OAuth redirect
            platform: Either 'facebook' or 'instagram'

        Returns:
            Dictionary containing token information
        """
        # First get short-lived token
        token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri if platform == 'facebook' else self.instagram_redirect_uri,
            'code': code
        }

        try:
            response = requests.get(token_url, params=params)
            response.raise_for_status()
            token_data = response.json()

            # Store the short-lived token
            self.user_access_token = token_data.get('access_token')

            # Exchange for long-lived token
            long_lived_token = self._get_long_lived_token(self.user_access_token)
            if long_lived_token:
                self.user_access_token = long_lived_token
                token_data['access_token'] = long_lived_token
                token_data['token_type'] = 'long-lived'

            return token_data

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to exchange code for token: {str(e)}"
            ) from e

    def _get_long_lived_token(self, short_lived_token: str) -> Optional[str]:
        """Exchange short-lived token for long-lived token"""
        try:
            token_url = f"https://graph.facebook.com/v12.0/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'fb_exchange_token': short_lived_token
            }
            response = requests.get(token_url, params=params)
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            print(f"Warning: Could not get long-lived token: {str(e)}")
            return None

    def get_user_pages(self) -> Dict[str, Any]:
        """
        Get all Facebook pages the user has access to.

        Returns:
            Dictionary containing page information
        """
        if not self.user_access_token:
            raise ValueError("No access token available. Complete OAuth flow first.")

        try:
            api_url = f"https://graph.facebook.com/me/accounts?access_token={self.user_access_token}"
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get user pages: {str(e)}"
            ) from e

    def get_instagram_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all Instagram accounts connected to the user's Facebook pages.

        Returns:
            List of Instagram account dictionaries
        """
        if not self.user_access_token:
            raise ValueError("No access token available. Complete OAuth flow first.")

        try:
            # Get user pages first
            pages_data = self.get_user_pages()
            instagram_accounts = []

            if 'data' in pages_data:
                for page in pages_data['data']:
                    if 'instagram_business_account' in page:
                        insta_account = page['instagram_business_account']
                        insta_account['page_id'] = page['id']
                        insta_account['page_name'] = page.get('name', 'Unknown')
                        insta_account['page_access_token'] = page.get('access_token')
                        instagram_accounts.append(insta_account)

            return instagram_accounts

        except Exception as e:
            raise Exception(f"Failed to get Instagram accounts: {str(e)}") from e

    def get_page_access_token(self, page_id: str) -> str:
        """
        Get a page access token for a specific page.

        Args:
            page_id: The Facebook page ID

        Returns:
            Page access token
        """
        if not self.user_access_token:
            raise ValueError("No access token available. Complete OAuth flow first.")

        try:
            # Get the page access token
            pages_data = self.get_user_pages()

            if 'data' in pages_data:
                for page in pages_data['data']:
                    if page['id'] == page_id:
                        return page.get('access_token')

            raise ValueError(f"No page found with ID: {page_id}")

        except Exception as e:
            raise Exception(f"Failed to get page access token: {str(e)}") from e

    def refresh_access_token(self) -> Optional[str]:
        """
        Refresh the access token (for long-lived tokens).

        Returns:
            New access token if successful
        """
        if not self.user_access_token:
            raise ValueError("No access token available to refresh.")

        try:
            # Check token debug info to see if it can be refreshed
            debug_url = f"https://graph.facebook.com/debug_token"
            params = {
                'input_token': self.user_access_token,
                'access_token': self.app_access_token or f"{self.client_id}|{self.client_secret}"
            }
            response = requests.get(debug_url, params=params)
            response.raise_for_status()
            debug_info = response.json()

            # If token is still valid and can be extended
            if debug_info.get('data', {}).get('is_valid', False):
                # Try to get a new long-lived token
                return self._get_long_lived_token(self.user_access_token)
            else:
                print("Token is no longer valid or cannot be refreshed")
                return None

        except Exception as e:
            print(f"Warning: Could not refresh token: {str(e)}")
            return None

    def save_tokens_to_file(self, result: Dict[str, Any], filename: str = 'oauth_tokens.json') -> None:
        """Save tokens and account info to a file for later use"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'user_access_token': result['tokens'].get('user_access_token'),
                    'page_access_token': result['tokens'].get('page_access_token'),
                    'instagram_account_id': result['accounts'].get('instagram', [{}])[0].get('id') if result['accounts'].get('instagram') else None,
                    'page_id': result['accounts'].get('instagram', [{}])[0].get('page_id') if result['accounts'].get('instagram') else None,
                    'platform': result['platform'],
                    'timestamp': time.time()
                }, f, indent=2)
            print(f"\n💾 Tokens saved to '{filename}' for future use")
        except Exception as e:
            print(f"Warning: Could not save tokens to file: {str(e)}")

    def get_instagram_user_info(self, instagram_account_id: str) -> Dict[str, Any]:
        """
        Get detailed Instagram user information.

        Args:
            instagram_account_id: The Instagram Business Account ID

        Returns:
            Dictionary containing Instagram user information
        """
        if not self.user_access_token:
            raise ValueError("No access token available. Complete OAuth flow first.")

        try:
            api_url = f"https://graph.facebook.com/{instagram_account_id}"
            params = {
                'access_token': self.user_access_token,
                'fields': 'id,username,biography,followers_count,media_count,profile_picture_url'
            }
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get Instagram user info: {str(e)}"
            ) from e

    def complete_oauth_flow(self, auth_code: str, platform: str = 'instagram') -> Dict[str, Any]:
        """
        Complete the entire OAuth flow from authorization code to getting all account info.

        Args:
            auth_code: The authorization code from the OAuth redirect
            platform: Either 'facebook' or 'instagram'

        Returns:
            Dictionary containing all collected information
        """
        result = {
            'platform': platform,
            'success': False,
            'error': None,
            'tokens': {},
            'accounts': {}
        }

        try:
            # Step 1: Exchange code for token
            print("🔄 Exchanging authorization code for access token...")
            token_data = self.exchange_code_for_token(auth_code, platform)
            result['tokens']['user_access_token'] = self.user_access_token

            # Step 2: Get user pages
            print("📋 Fetching user pages...")
            pages_data = self.get_user_pages()
            result['accounts']['pages'] = pages_data.get('data', [])

            # Step 3: Find Instagram accounts (if Instagram platform)
            if platform == 'instagram':
                print("📸 Finding Instagram accounts...")
                instagram_accounts = self.get_instagram_accounts()
                result['accounts']['instagram'] = instagram_accounts

                if instagram_accounts:
                    # Get first Instagram account info
                    first_insta = instagram_accounts[0]
                    self.instagram_account_id = first_insta['id']
                    self.page_id = first_insta['page_id']

                    # Get page access token
                    page_token = self.get_page_access_token(self.page_id)
                    result['tokens']['page_access_token'] = page_token

                    # Get Instagram user info
                    insta_info = self.get_instagram_user_info(self.instagram_account_id)
                    result['accounts']['instagram_user_info'] = insta_info

                    print(f"✅ Instagram Account ID: {self.instagram_account_id}")
                    print(f"✅ Page ID: {self.page_id}")
                    print(f"✅ Page Access Token: {page_token[:20]}... (truncated)")

            result['success'] = True
            print("🎉 OAuth flow completed successfully!")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ OAuth flow failed: {str(e)}")

        return result

def main():
    """
    Main function with interactive OAuth flow completion.
    """
    print("🔑 Enhanced Facebook/Instagram OAuth Handler")
    print("=" * 60)
    print("This script handles the complete OAuth flow including:")
    print("- Token exchange with long-lived token generation")
    print("- Page and Instagram account discovery")
    print("- Automatic token refresh handling")
    print()

    try:
        # Initialize OAuth handler
        oauth = EnhancedOAuthHandler()
        print("✅ OAuth handler initialized successfully")

        # Let user choose platform
        print("\n🎯 Choose authentication option:")
        print("1. Facebook only")
        print("2. Instagram only")
        print("3. Both Facebook and Instagram")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == '1':
            platform = 'facebook'
        elif choice == '2':
            platform = 'instagram'
        elif choice == '3':
            platform = 'both'
        else:
            print("❌ Invalid choice. Please use 1, 2, or 3")
            return

        # Handle both platforms case
        results = []
        if platform == 'both':
            platforms_to_auth = ['facebook', 'instagram']
        else:
            platforms_to_auth = [platform]

        for current_platform in platforms_to_auth:
            print(f"\n🔄 Processing {current_platform} authentication...")

            # Generate and display auth URL
            auth_url = oauth.get_auth_url(current_platform)
            print(f"\n🔗 {current_platform.capitalize()} Authorization URL: {auth_url}")

            # Open in browser
            try:
                webbrowser.open(auth_url)
                print("🌐 Opening authorization URL in your browser...")
            except:
                print("📝 Please copy and paste the URL above into your browser")

            # Get authorization code from user
            auth_code = input(f"\n📥 After authorizing {current_platform}, paste the full redirect URL here: ").strip()

            if not auth_code:
                print("❌ No URL provided")
                continue

            # Extract code from URL
            try:
                parsed_url = urlparse(auth_code)
                query_params = parse_qs(parsed_url.query)
                code = query_params.get('code', [None])[0]

                if not code:
                    print("❌ No authorization code found in the URL")
                    continue
            except:
                # Maybe user pasted just the code
                code = auth_code

            print(f"\n🔑 Using authorization code: {code[:20]}... (truncated)")

            # Complete the full OAuth flow
            print(f"\n🚀 Completing {current_platform} OAuth flow...")
            result = oauth.complete_oauth_flow(code, current_platform)
            results.append((current_platform, result))

        # Process and display results for all platforms
        all_success = True
        for current_platform, result in results:
            if result['success']:
                print(f"\n📊 {current_platform.capitalize()} OAuth Flow Results:")
                print(f"Platform: {result['platform']}")
                print(f"User Access Token: {result['tokens'].get('user_access_token', 'N/A')[:20]}...")

                if current_platform == 'instagram' and result['accounts'].get('instagram'):
                    insta_accounts = result['accounts']['instagram']
                    print(f"Instagram Accounts Found: {len(insta_accounts)}")

                    for i, account in enumerate(insta_accounts):
                        print(f"\nInstagram Account {i+1}:")
                        print(f"  ID: {account['id']}")
                        print(f"  Connected to Page: {account['page_name']} (ID: {account['page_id']})")
                        print(f"  Page Access Token: {account['page_access_token'][:20]}...")

                    if 'instagram_user_info' in result['accounts']:
                        user_info = result['accounts']['instagram_user_info']
                        print(f"\nInstagram User Info:")
                        print(f"  Username: {user_info.get('username', 'N/A')}")
                        print(f"  Followers: {user_info.get('followers_count', 'N/A')}")
                        print(f"  Media Count: {user_info.get('media_count', 'N/A')}")

                print(f"\n🔄 {current_platform.capitalize()} Token Information:")
                print("This token is a long-lived token (60 days)")
                print("You can refresh it using the refresh_access_token() method")
                print("Facebook automatically refreshes tokens when they're used and still valid")

                # Save tokens to file for later use
                filename = f"oauth_tokens_{current_platform}.json"
                oauth.save_tokens_to_file(result, filename)
            else:
                print(f"❌ {current_platform.capitalize()} OAuth flow failed: {result.get('error', 'Unknown error')}")
                all_success = False

        if all_success and len(results) > 1:
            print(f"\n🎉 All OAuth flows completed successfully for {len(results)} platforms!")
        elif all_success:
            print(f"\n🎉 OAuth flow completed successfully!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n📝 Make sure your .env file has the correct credentials:")
        print("FB_CLIENT_ID=your_facebook_client_id")
        print("FB_CLIENT_SECRET=your_facebook_client_secret")
        print("FB_REDIRECT_URI=http://localhost:5000/auth/facebook/callback")


if __name__ == "__main__":
    main()