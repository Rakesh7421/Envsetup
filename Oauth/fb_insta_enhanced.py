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
            scope = "email,public_profile,pages_show_list,pages_read_engagement,pages_manage_posts,pages_manage_engagement"
        elif platform.lower() == 'instagram':
            base_url = "https://www.facebook.com/v12.0/dialog/oauth"
            redirect_uri = self.instagram_redirect_uri
            scope = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,instagram_manage_insights,pages_manage_posts,pages_manage_engagement"
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
            pages_data = response.json()

            # Log the number of pages found
            if 'data' in pages_data:
                print(f"📋 Found {len(pages_data['data'])} Facebook pages")
                for page in pages_data['data']:
                    print(f"  - {page.get('name', 'Unnamed Page')} (ID: {page['id']})")
            else:
                print("📋 No Facebook pages found or unexpected response format")

            return pages_data
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get user pages: {str(e)}")
            print("💡 This could be due to:")
            print("   - Missing 'pages_show_list' permission")
            print("   - Invalid access token")
            print("   - User has no Facebook pages")
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

    def extract_ids_from_token_debug(self) -> Dict[str, Any]:
        """
        Extract page ID and Instagram account ID from token debug information.
        This is used as a fallback when regular methods don't find pages.

        Returns:
            Dictionary containing extracted IDs
        """
        if not self.user_access_token:
            return {'page_id': None, 'instagram_account_id': None}

        try:
            debug_url = f"https://graph.facebook.com/debug_token"
            params = {
                'input_token': self.user_access_token,
                'access_token': self.app_access_token or f"{self.client_id}|{self.client_secret}"
            }
            response = requests.get(debug_url, params=params)
            response.raise_for_status()
            debug_info = response.json()

            page_id = None
            instagram_account_id = None

            # Look through granular scopes for page and instagram IDs
            granular_scopes = debug_info.get('data', {}).get('granular_scopes', [])

            for scope in granular_scopes:
                if scope.get('scope') in ['pages_show_list', 'pages_read_engagement', 'pages_manage_posts', 'pages_manage_engagement']:
                    target_ids = scope.get('target_ids', [])
                    if target_ids and not page_id:
                        page_id = target_ids[0]
                        print(f"🎯 Found Page ID from token debug: {page_id}")

                elif scope.get('scope') in ['instagram_basic', 'instagram_manage_comments', 'instagram_manage_insights', 'instagram_content_publish']:
                    target_ids = scope.get('target_ids', [])
                    if target_ids and not instagram_account_id:
                        instagram_account_id = target_ids[0]
                        print(f"🎯 Found Instagram Account ID from token debug: {instagram_account_id}")

            return {
                'page_id': page_id,
                'instagram_account_id': instagram_account_id
            }

        except Exception as e:
            print(f"Warning: Could not extract IDs from token debug: {str(e)}")
            return {'page_id': None, 'instagram_account_id': None}

    def save_tokens_to_file(self, result: Dict[str, Any], filename: str = 'oauth_tokens.json') -> None:
        """Save tokens and account info to a file for later use"""
        try:
            # Initialize variables
            user_access_token = result['tokens'].get('user_access_token')
            page_access_token = result['tokens'].get('page_access_token')
            instagram_account_id = None
            page_id = None

            # Handle Instagram platform
            if result['platform'] == 'instagram' and result['accounts'].get('instagram'):
                instagram_accounts = result['accounts']['instagram']
                if instagram_accounts:
                    instagram_account_id = instagram_accounts[0].get('id')
                    page_id = instagram_accounts[0].get('page_id')

            # Handle Facebook platform - get first page if available
            elif result['platform'] == 'facebook' and result['accounts'].get('pages'):
                pages = result['accounts']['pages']
                if pages:
                    page_id = pages[0].get('id')
                    # Try to get page access token if available
                    if not page_access_token:
                        page_access_token = pages[0].get('access_token')

            # NEW: Fallback - Use IDs from token debug extraction if not found through regular methods
            if not instagram_account_id and self.instagram_account_id:
                instagram_account_id = self.instagram_account_id
            if not page_id and self.page_id:
                page_id = self.page_id

            with open(filename, 'w') as f:
                json.dump({
                    'user_access_token': user_access_token,
                    'page_access_token': page_access_token,
                    'instagram_account_id': instagram_account_id,
                    'page_id': page_id,
                    'platform': result['platform'],
                    'timestamp': time.time()
                }, f, indent=2)
            print(f"\n💾 Tokens saved to '{filename}' for future use")
        except Exception as e:
            print(f"Warning: Could not save tokens to file: {str(e)}")

    def get_page_token_info(self, page_access_token: str) -> Dict[str, Any]:
        """
        Get detailed information about a page access token.

        Args:
            page_access_token: The page access token to inspect

        Returns:
            Dictionary containing token debug information
        """
        try:
            debug_url = "https://graph.facebook.com/debug_token"
            params = {
                'input_token': page_access_token,
                'access_token': self.app_access_token or f"{self.client_id}|{self.client_secret}"
            }
            response = requests.get(debug_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get page token info: {str(e)}"
            ) from e

    def refresh_page_access_token(self, page_id: str) -> Optional[str]:
        """
        Refresh a page access token by refreshing the user token and getting new page token.

        Args:
            page_id: The Facebook page ID

        Returns:
            New page access token if successful, None otherwise
        """
        try:
            # First refresh the user access token
            refreshed_user_token = self.refresh_access_token()
            if not refreshed_user_token:
                return None

            # Update the user access token
            self.user_access_token = refreshed_user_token

            # Get the refreshed page access token
            return self.get_page_access_token(page_id)

        except Exception as e:
            print(f"❌ Failed to refresh page access token: {str(e)}")
            return None

    def check_page_token_permissions(self, page_access_token: str) -> List[str]:
        """
        Check what permissions a page access token has.

        Args:
            page_access_token: The page access token to check

        Returns:
            List of permission strings
        """
        try:
            token_info = self.get_page_token_info(page_access_token)
            data = token_info.get('data', {})
            return data.get('scopes', [])
        except Exception as e:
            print(f"Warning: Could not check page token permissions: {str(e)}")
            return []

    def get_all_page_tokens_with_permissions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all page access tokens with their permissions and expiry info.

        Returns:
            Dictionary of page tokens with metadata
        """
        try:
            # Get all pages
            pages_data = self.get_user_pages()
            page_tokens_info = {}

            if 'data' in pages_data:
                for page in pages_data['data']:
                    page_id = page['id']
                    page_name = page.get('name', 'Unknown')
                    page_token = page.get('access_token')

                    if page_token:
                        # Get token info
                        token_info = self.get_page_token_info(page_token)
                        data = token_info.get('data', {})

                        page_tokens_info[page_id] = {
                            'page_name': page_name,
                            'page_access_token': page_token,
                            'scopes': data.get('scopes', []),
                            'expires_at': data.get('expires_at'),
                            'is_valid': data.get('is_valid', False),
                            'instagram_business_account': page.get('instagram_business_account')
                        }

            return page_tokens_info

        except Exception as e:
            print(f"Warning: Could not get page tokens with permissions: {str(e)}")
            return {}

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

    def complete_oauth_flow(self, auth_code: str, platform: str = 'both') -> Dict[str, Any]:
        """
        Complete the entire OAuth flow from authorization code to getting all account info.
        Now supports unified authentication for both Facebook and Instagram.

        Args:
            auth_code: The authorization code from the OAuth redirect
            platform: Either 'facebook', 'instagram', or 'both' (default)

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

            # Step 2: Get user pages (always do this for both platforms)
            print("📋 Fetching user pages...")
            pages_data = self.get_user_pages()
            result['accounts']['pages'] = pages_data.get('data', [])

            # Step 3: Process based on platform
            if platform in ['instagram', 'both']:
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

            # For Facebook platform or if no Instagram accounts found, use first Facebook page
            if platform in ['facebook', 'both']:
                if not self.page_id and result['accounts']['pages']:
                    first_page = result['accounts']['pages'][0]
                    self.page_id = first_page['id']

                    # Get page access token if not already set
                    if not result['tokens'].get('page_access_token'):
                        page_token = first_page.get('access_token')
                        if page_token:
                            result['tokens']['page_access_token'] = page_token
                            print(f"✅ Facebook Page ID: {self.page_id}")
                            print(f"✅ Page Access Token: {page_token[:20]}... (truncated)")
                        else:
                            print(f"✅ Facebook Page ID: {self.page_id} (no separate page token available)")

            # NEW: Fallback - Extract IDs from token debug info if not found through regular methods
            if (platform in ['instagram', 'both'] and not self.instagram_account_id) or \
               (platform in ['facebook', 'both'] and not self.page_id):
                print("\n🔍 No pages found through regular methods, checking token debug info...")
                debug_ids = self.extract_ids_from_token_debug()

                if debug_ids['page_id'] and not self.page_id:
                    self.page_id = debug_ids['page_id']
                    print(f"✅ Found Page ID from token debug: {self.page_id}")

                    # Try to get page access token for this page
                    try:
                        page_token = self.get_page_access_token(self.page_id)
                        if page_token:
                            result['tokens']['page_access_token'] = page_token
                            print(f"✅ Page Access Token: {page_token[:20]}... (truncated)")
                    except:
                        print(f"⚠️ Could not get page access token for page {self.page_id}")

                if debug_ids['instagram_account_id'] and not self.instagram_account_id:
                    self.instagram_account_id = debug_ids['instagram_account_id']
                    print(f"✅ Found Instagram Account ID from token debug: {self.instagram_account_id}")

                    # Add to result for saving
                    if 'instagram' not in result['accounts']:
                        result['accounts']['instagram'] = [{
                            'id': self.instagram_account_id,
                            'page_id': self.page_id
                        }]

            # NEW: Try to get page access token for the page ID we found
            if self.page_id and not result['tokens'].get('page_access_token'):
                print(f"\n🔑 Attempting to get page access token for page {self.page_id}...")
                try:
                    # Try to get page access token via Graph API
                    api_url = f"https://graph.facebook.com/{self.page_id}"
                    params = {
                        'access_token': self.user_access_token,
                        'fields': 'access_token',
                        'metadata': '1'
                    }
                    response = requests.get(api_url, params=params)

                    if response.status_code == 200:
                        page_data = response.json()
                        if 'access_token' in page_data:
                            page_token = page_data['access_token']
                            result['tokens']['page_access_token'] = page_token
                            print(f"✅ Found page access token: {page_token[:20]}...")
                        else:
                            print("ℹ️  No separate page access token found, will use user access token")
                    else:
                        print(f"⚠️  Could not get page access token: {response.status_code}")
                        print("ℹ️  Will use user access token for posting")

                except Exception as e:
                    print(f"⚠️  Could not get page access token: {str(e)}")
                    print("ℹ️  Will use user access token for posting")

            result['success'] = True
            print("🎉 OAuth flow completed successfully!")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ OAuth flow failed: {str(e)}")

        return result

def main():
    """
    Main function with simplified unified OAuth flow.
    Now requires only ONE authentication for both Facebook and Instagram access.
    """
    print("🔑 Enhanced Facebook/Instagram OAuth Handler")
    print("=" * 60)
    print("This script handles the complete OAuth flow including:")
    print("- Single authentication for both Facebook and Instagram")
    print("- Token exchange with long-lived token generation")
    print("- Automatic page and Instagram account discovery")
    print("- Automatic token refresh handling")
    print()

    try:
        # Initialize OAuth handler
        oauth = EnhancedOAuthHandler()
        print("✅ OAuth handler initialized successfully")

        # Simplified choice - just ask for platform preference but use unified auth
        print("\n🎯 What do you want to access?")
        print("1. Facebook only")
        print("2. Instagram only")
        print("3. Both Facebook and Instagram (recommended)")

        choice = input("Enter your choice (1/2/3): ").strip() or '3'

        if choice == '1':
            platform = 'facebook'
        elif choice == '2':
            platform = 'instagram'
        else:
            platform = 'both'

        print(f"\n🔄 Processing unified authentication for {platform} access...")

        # Generate auth URL with comprehensive permissions for both platforms
        auth_url = oauth.get_auth_url('instagram')  # Use Instagram scope which includes Facebook permissions
        print(f"\n🔗 Authorization URL: {auth_url}")
        print("📝 This single authentication will give access to both Facebook and Instagram")

        # Open in browser
        try:
            webbrowser.open(auth_url)
            print("🌐 Opening authorization URL in your browser...")
        except:
            print("📝 Please copy and paste the URL above into your browser")

        # Get authorization code from user - ONLY ONCE
        auth_code = input(f"\n📥 After authorizing, paste the full redirect URL here: ").strip()

        if not auth_code:
            print("❌ No URL provided")
            return

        # Extract code from URL
        try:
            parsed_url = urlparse(auth_code)
            query_params = parse_qs(parsed_url.query)
            code = query_params.get('code', [None])[0]

            if not code:
                print("❌ No authorization code found in the URL")
                return
        except:
            # Maybe user pasted just the code
            code = auth_code

        print(f"\n🔑 Using authorization code: {code[:20]}... (truncated)")

        # Complete the unified OAuth flow - ONLY ONCE
        print(f"\n🚀 Completing unified OAuth flow...")
        result = oauth.complete_oauth_flow(code, platform)

        if result['success']:
            print(f"\n📊 Unified OAuth Flow Results:")
            print(f"Platform: {result['platform']}")
            print(f"User Access Token: {result['tokens'].get('user_access_token', 'N/A')[:20]}...")

            # Show Facebook page info if available
            if result['accounts']['pages']:
                print(f"\n📋 Facebook Pages Found: {len(result['accounts']['pages'])}")
                for i, page in enumerate(result['accounts']['pages']):
                    print(f"  {i+1}. {page.get('name', 'Unnamed Page')} (ID: {page['id']})")

                if oauth.page_id:
                    print(f"\n✅ Selected Page ID: {oauth.page_id}")

            # Show Instagram info if available
            if result['accounts'].get('instagram'):
                insta_accounts = result['accounts']['instagram']
                print(f"\n📸 Instagram Accounts Found: {len(insta_accounts)}")

                for i, account in enumerate(insta_accounts):
                    print(f"  {i+1}. Instagram ID: {account['id']} (Connected to Page: {account['page_name']})")

                if oauth.instagram_account_id:
                    print(f"\n✅ Selected Instagram Account ID: {oauth.instagram_account_id}")

            # Show token info
            if result['tokens'].get('page_access_token'):
                page_token = result['tokens']['page_access_token']
                print(f"\n🔑 Page Access Token: {page_token[:20]}... (truncated)")

                # Check permissions
                permissions = oauth.check_page_token_permissions(page_token)
                if permissions:
                    print(f"Permissions: {', '.join(permissions)}")
                    posting_permissions = [p for p in permissions if any(perm in p for perm in ['publish', 'manage_posts', 'manage_engagement'])]
                    if posting_permissions:
                        print(f"✅ Posting Permissions: {', '.join(posting_permissions)}")

            # Save tokens to appropriate files
            if platform == 'both':
                # Save to both files for compatibility
                oauth.save_tokens_to_file(result, 'oauth_tokens_facebook.json')
                oauth.save_tokens_to_file(result, 'oauth_tokens_instagram.json')
                print(f"\n💾 Tokens saved to both 'oauth_tokens_facebook.json' and 'oauth_tokens_instagram.json'")
            else:
                filename = f"oauth_tokens_{platform}.json"
                oauth.save_tokens_to_file(result, filename)
                print(f"\n💾 Tokens saved to '{filename}'")

            print(f"\n🎉 Unified OAuth flow completed successfully!")
            print("💡 You now have access to both Facebook and Instagram with a single authentication!")

        else:
            print(f"❌ OAuth flow failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n📝 Make sure your .env file has the correct credentials:")
        print("FB_CLIENT_ID=your_facebook_client_id")
        print("FB_CLIENT_SECRET=your_facebook_client_secret")
        print("FB_REDIRECT_URI=http://localhost:5000/auth/facebook/callback")


if __name__ == "__main__":
    main()