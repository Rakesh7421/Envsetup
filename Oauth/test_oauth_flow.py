#!/usr/bin/env python3
"""
Test script to demonstrate the OAuth flow step by step.
This script shows how to use the OAuth handler to complete the authentication process.
"""

import sys
import webbrowser
from fb_insta import OAuthHandler
from urllib.parse import urlparse, parse_qs

def test_oauth_flow():
    """
    Test the complete OAuth flow interactively.
    """
    print("🔑 Facebook/Instagram OAuth Flow Test")
    print("=" * 50)

    try:
        # Initialize OAuth handler
        oauth = OAuthHandler()
        print("✅ OAuth handler initialized successfully")

        # Let user choose platform
        platform = input("Choose platform (facebook/instagram): ").strip().lower()
        if platform not in ['facebook', 'instagram']:
            print("❌ Invalid platform. Please use 'facebook' or 'instagram'")
            return

        # Generate auth URL
        auth_url = oauth.get_auth_url(platform)
        print(f"\n🔗 Authorization URL: {auth_url}")

        # Open in browser
        try:
            webbrowser.open(auth_url)
            print("🌐 Opening authorization URL in your browser...")
        except:
            print("📝 Please copy and paste the URL above into your browser")

        # Get authorization code from user
        auth_code = input("\n📥 After authorizing, paste the 'code' parameter from the redirect URL here: ").strip()

        if not auth_code:
            print("❌ No authorization code provided")
            return

        # Exchange code for token
        print("\n🔄 Exchanging authorization code for access token...")
        try:
            token_data = oauth.exchange_code_for_token(auth_code, platform)
            access_token = token_data.get('access_token')

            if not access_token:
                print("❌ Failed to get access token")
                print(f"Response: {token_data}")
                return

            print(f"✅ Access Token: {access_token[:20]}... (truncated)")

            # Get user info
            if platform == 'facebook':
                print("\n👤 Fetching Facebook user information...")
                user_info = oauth.get_user_info(access_token, 'facebook')
                print(f"📋 User Info: {user_info}")
            else:  # instagram
                print("\n👤 Fetching Instagram user accounts...")
                accounts_info = oauth.get_user_info(access_token, 'instagram')

                if 'data' in accounts_info and len(accounts_info['data']) > 0:
                    # Find Instagram business account
                    insta_account = None
                    for account in accounts_info['data']:
                        if 'instagram_business_account' in account:
                            insta_account = account['instagram_business_account']
                            break

                    if insta_account:
                        print(f"📋 Found Instagram Business Account: {insta_account['id']}")
                        print("\n📸 Fetching Instagram user information...")
                        insta_user_info = oauth.get_instagram_user_info(access_token, insta_account['id'])
                        print(f"📋 Instagram User Info: {insta_user_info}")
                    else:
                        print("❌ No Instagram Business Account found. Make sure your Instagram is connected to a Facebook Page.")
                else:
                    print("❌ No accounts found. Make sure you have the right permissions.")

        except Exception as e:
            print(f"❌ Error during token exchange: {str(e)}")

    except Exception as e:
        print(f"❌ Initialization error: {str(e)}")
        print("\n📝 Make sure your .env file has the correct credentials:")
        print("FB_CLIENT_ID=your_facebook_client_id")
        print("FB_CLIENT_SECRET=your_facebook_client_secret")
        print("FB_REDIRECT_URI=http://localhost:5000/auth/facebook/callback")

def main():
    """
    Main function to run the OAuth flow test.
    """
    print("🚀 Starting OAuth Flow Test")
    print("This script will guide you through the Facebook/Instagram OAuth process")
    print("Make sure you have a local server running on port 5000 to handle the redirect")

    # Start the test
    test_oauth_flow()

    print("\n🎉 OAuth flow test completed!")

if __name__ == "__main__":
    main()