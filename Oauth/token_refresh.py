#!/usr/bin/env python3
"""
Facebook/Instagram Token Refresh Utility
This script explains Facebook token refresh mechanics and provides tools to refresh tokens.
"""

import os
import json
import time
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()

class TokenRefreshManager:
    """
    Manages Facebook/Instagram token refresh operations.
    """

    def __init__(self):
        """
        Initialize the token manager with credentials from .env
        """
        self.client_id = os.getenv('FB_CLIENT_ID')
        self.client_secret = os.getenv('FB_CLIENT_SECRET')
        self.app_access_token = f"{self.client_id}|{self.client_secret}"

        if not self.client_id or not self.client_secret:
            raise EnvironmentError("Missing FB_CLIENT_ID or FB_CLIENT_SECRET in .env file")

    def load_tokens_from_file(self, filename: str = 'oauth_tokens.json') -> Optional[Dict[str, Any]]:
        """
        Load tokens from a JSON file.

        Args:
            filename: Name of the file to load tokens from

        Returns:
            Dictionary containing token data, or None if file doesn't exist
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load tokens from {filename}: {str(e)}")
            return None

    def get_token_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get detailed information about an access token using Facebook's debug endpoint.

        Args:
            access_token: The access token to inspect

        Returns:
            Dictionary containing token debug information
        """
        try:
            debug_url = "https://graph.facebook.com/debug_token"
            params = {
                'input_token': access_token,
                'access_token': self.app_access_token
            }
            response = requests.get(debug_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to get token info: {str(e)}"
            ) from e

    def refresh_long_lived_token(self, access_token: str) -> Optional[str]:
        """
        Refresh a long-lived access token.

        Args:
            access_token: The long-lived access token to refresh

        Returns:
            New access token if successful, None otherwise
        """
        try:
            # First check if the token is still valid and can be refreshed
            token_info = self.get_token_info(access_token)
            data = token_info.get('data', {})

            if not data.get('is_valid', False):
                print("❌ Token is no longer valid and cannot be refreshed")
                return None

            # Check if token is long-lived (expires > 1 day)
            expires_in = data.get('expires_at', 0)
            if expires_in:
                current_time = int(time.time())
                time_left = expires_in - current_time
                days_left = time_left / (24 * 3600)

                if days_left < 1:
                    print("⚠️  Token is short-lived or about to expire. Cannot refresh.")
                    return None

            # Attempt to refresh the token
            refresh_url = "https://graph.facebook.com/v12.0/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'fb_exchange_token': access_token
            }

            response = requests.get(refresh_url, params=params)
            response.raise_for_status()
            new_token_data = response.json()

            return new_token_data.get('access_token')

        except Exception as e:
            print(f"❌ Failed to refresh token: {str(e)}")
            return None

    def check_token_expiry(self, access_token: str) -> Dict[str, Any]:
        """
        Check when a token will expire and provide refresh recommendations.

        Args:
            access_token: The access token to check

        Returns:
            Dictionary with expiry information and recommendations
        """
        try:
            token_info = self.get_token_info(access_token)
            data = token_info.get('data', {})

            if not data.get('is_valid', False):
                return {
                    'valid': False,
                    'error': 'Token is not valid',
                    'recommendation': 'Re-authenticate to get a new token'
                }

            expires_at = data.get('expires_at', 0)
            if not expires_at:
                return {
                    'valid': True,
                    'error': 'No expiry information available',
                    'recommendation': 'Token may be app access token (no expiry)'
                }

            current_time = int(time.time())
            time_left = expires_at - current_time
            days_left = time_left / (24 * 3600)
            hours_left = time_left / 3600

            # Determine refresh recommendation
            if days_left > 30:
                recommendation = "✅ Token is valid. No refresh needed yet."
            elif days_left > 7:
                recommendation = "🟡 Token will expire soon. Consider refreshing."
            elif days_left > 1:
                recommendation = "🟠 Token expires soon. Should refresh now."
            else:
                recommendation = "🔴 Token expires very soon. Refresh immediately!"

            return {
                'valid': True,
                'expires_at': datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S'),
                'time_left_seconds': time_left,
                'days_left': days_left,
                'hours_left': hours_left,
                'recommendation': recommendation,
                'token_type': 'long-lived' if days_left > 1 else 'short-lived',
                'scopes': data.get('scopes', [])
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'recommendation': 'Could not determine token status'
            }

def print_token_refresh_guide():
    """Print a comprehensive guide about Facebook token refresh"""
    print("📚 FACEBOOK/INSTAGRAM TOKEN REFRESH GUIDE")
    print("=" * 60)

    print("\n🔑 TOKEN TYPES:")
    print("- Short-lived tokens: ~1 hour expiry (from initial OAuth)")
    print("- Long-lived tokens: ~60 days expiry (from token exchange)")
    print("- App tokens: No expiry (for app-level operations)")

    print("\n🔄 HOW TOKEN REFRESH WORKS:")
    print("1. Initial OAuth gives you a short-lived token (~1 hour)")
    print("2. Exchange short-lived token for long-lived token (~60 days)")
    print("3. Long-lived tokens can be refreshed before they expire")
    print("4. Facebook automatically extends tokens when used (if still valid)")

    print("\n⏳ WHEN TO REFRESH:")
    print("- Long-lived tokens: Refresh before 60 days expire")
    print("- Best practice: Refresh when < 30 days remaining")
    print("- Automatic extension: Facebook extends tokens when used")
    print("- Manual refresh: Use this script when needed")

    print("\n🔄 REFRESH REQUIREMENTS:")
    print("- Token must still be valid (not expired)")
    print("- Token must be long-lived (not short-lived)")
    print("- Requires client_id and client_secret")
    print("- User must still have authorized your app")

    print("\n📅 TOKEN EXTENSION RULES:")
    print("- Tokens are automatically extended when used")
    print("- Extension period: Up to 60 days from last use")
    print("- No extension if: Token expired, user deauthorized app")
    print("- Manual refresh gives new 60-day window")

    print("\n⚠️ IMPORTANT NOTES:")
    print("- You DON'T need to re-run OAuth to refresh tokens")
    print("- This script can refresh tokens without user interaction")
    print("- Store tokens securely and refresh them periodically")
    print("- Monitor token expiry to avoid service interruptions")

def main():
    """Main function for token refresh utility"""
    print("🔄 Facebook/Instagram Token Refresh Utility")
    print("=" * 60)

    # Print the guide first
    print_token_refresh_guide()

    try:
        # Initialize token manager
        token_manager = TokenRefreshManager()
        print("\n✅ Token refresh manager initialized")

        # Find available token files
        token_files = []
        for filename in ['oauth_tokens.json', 'oauth_tokens_facebook.json', 'oauth_tokens_instagram.json']:
            if os.path.exists(filename):
                token_files.append(filename)

        if not token_files:
            print("\n❌ No token files found. Please run the OAuth flow first.")
            return

        print(f"\n📁 Found {len(token_files)} token file(s):")
        for i, filename in enumerate(token_files, 1):
            print(f"  {i}. {filename}")

        # Let user choose which token to check/refresh
        if len(token_files) == 1:
            chosen_file = token_files[0]
        else:
            choice = input(f"\n📥 Choose token file to process (1-{len(token_files)}): ").strip()
            try:
                chosen_file = token_files[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return

        # Load and analyze the token
        print(f"\n🔍 Analyzing token from {chosen_file}...")
        token_data = token_manager.load_tokens_from_file(chosen_file)

        if not token_data:
            print("❌ Could not load token data")
            return

        access_token = token_data.get('user_access_token')
        if not access_token:
            print("❌ No access token found in file")
            return

        # Check token expiry status
        expiry_info = token_manager.check_token_expiry(access_token)

        print("\n📊 TOKEN STATUS REPORT:")
        print(f"Valid: {'✅ Yes' if expiry_info.get('valid') else '❌ No'}")
        if expiry_info.get('valid'):
            print(f"Token Type: {expiry_info.get('token_type', 'unknown')}")
            print(f"Expires At: {expiry_info.get('expires_at', 'unknown')}")
            print(f"Time Left: {expiry_info.get('days_left', 0):.1f} days ({expiry_info.get('hours_left', 0):.1f} hours)")
            print(f"Scopes: {', '.join(expiry_info.get('scopes', []))}")
            print(f"Recommendation: {expiry_info.get('recommendation', 'Unknown')}")

            # Ask if user wants to refresh
            if expiry_info.get('days_left', 0) < 60:  # Only offer refresh if < 60 days left
                refresh_choice = input("\n🔄 Do you want to refresh this token? (y/n): ").strip().lower()
                if refresh_choice == 'y':
                    print("🔄 Attempting to refresh token...")

                    # Try to refresh the token
                    new_token = token_manager.refresh_long_lived_token(access_token)

                    if new_token:
                        print("✅ Token refreshed successfully!")

                        # Update the token data
                        token_data['user_access_token'] = new_token
                        token_data['timestamp'] = time.time()

                        # Save the updated token
                        with open(chosen_file, 'w') as f:
                            json.dump(token_data, f, indent=2)

                        # Check the new token expiry
                        new_expiry_info = token_manager.check_token_expiry(new_token)
                        print(f"New Token Expires: {new_expiry_info.get('expires_at', 'unknown')}")
                        print(f"New Time Left: {new_expiry_info.get('days_left', 0):.1f} days")

                        print("\n💾 Updated token saved to file")
                    else:
                        print("❌ Token refresh failed")
                else:
                    print("🔄 Token refresh skipped")
            else:
                print("\n🔄 Token doesn't need refresh yet (60+ days remaining)")

        else:
            print(f"Error: {expiry_info.get('error', 'Unknown')}")
            print(f"Recommendation: {expiry_info.get('recommendation', 'Re-authenticate')}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()