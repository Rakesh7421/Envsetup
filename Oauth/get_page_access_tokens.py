#!/usr/bin/env python3
"""
Dedicated Page Access Token Extraction Script
This script focuses specifically on extracting Facebook and Instagram page access tokens.
"""

import os
import json
import webbrowser
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

class PageAccessTokenExtractor:
    """
    Specialized class for extracting Facebook and Instagram page access tokens.
    """

    def __init__(self):
        """
        Initialize with Facebook credentials.
        """
        self.client_id = os.getenv('FB_CLIENT_ID')
        self.client_secret = os.getenv('FB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('FB_REDIRECT_URI')

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise EnvironmentError("Missing required credentials in .env file")

        self.user_access_token = None
        self.page_access_tokens = {}  # Stores {page_id: page_access_token}
        self.instagram_accounts = []  # Stores Instagram accounts with page tokens

    def get_auth_url(self) -> str:
        """
        Get authorization URL with required scopes for page access.
        """
        scope = "email,public_profile,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
        return f"https://www.facebook.com/v12.0/dialog/oauth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}&response_type=code"

    def exchange_code_for_user_token(self, auth_code: str) -> str:
        """
        Exchange authorization code for user access token.
        """
        token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': auth_code
        }

        response = requests.get(token_url, params=params)
        response.raise_for_status()
        token_data = response.json()

        # Get long-lived token
        long_lived_url = f"https://graph.facebook.com/v12.0/oauth/access_token?grant_type=fb_exchange_token&client_id={self.client_id}&client_secret={self.client_secret}&fb_exchange_token={token_data['access_token']}"
        response = requests.get(long_lived_url)
        response.raise_for_status()

        self.user_access_token = response.json()['access_token']
        return self.user_access_token

    def get_all_page_access_tokens(self) -> Dict[str, str]:
        """
        Get ALL page access tokens the user has access to.
        This is the main method for extracting page access tokens.

        Returns:
            Dictionary of {page_id: page_access_token}
        """
        if not self.user_access_token:
            raise ValueError("No user access token available")

        # Get all pages the user manages
        pages_url = f"https://graph.facebook.com/me/accounts?access_token={self.user_access_token}&fields=id,name,access_token,instagram_business_account"
        response = requests.get(pages_url)
        response.raise_for_status()
        pages_data = response.json()

        page_tokens = {}
        instagram_accounts = []

        if 'data' in pages_data:
            for page in pages_data['data']:
                page_id = page['id']
                page_name = page.get('name', 'Unknown')
                page_token = page.get('access_token')

                if page_token:
                    page_tokens[page_id] = {
                        'page_access_token': page_token,
                        'page_name': page_name,
                        'instagram_business_account': page.get('instagram_business_account')
                    }

                    # Check if this page has an Instagram account connected
                    if 'instagram_business_account' in page:
                        insta_account = page['instagram_business_account']
                        insta_account['page_id'] = page_id
                        insta_account['page_name'] = page_name
                        insta_account['page_access_token'] = page_token
                        instagram_accounts.append(insta_account)

        self.page_access_tokens = page_tokens
        self.instagram_accounts = instagram_accounts

        return page_tokens

    def get_instagram_page_tokens(self) -> List[Dict[str, Any]]:
        """
        Get page access tokens specifically for Instagram-connected pages.

        Returns:
            List of Instagram accounts with their connected page tokens
        """
        return self.instagram_accounts

    def save_page_tokens_to_file(self, filename: str = 'page_access_tokens.json') -> None:
        """
        Save all extracted page access tokens to a file.
        """
        data_to_save = {
            'user_access_token': self.user_access_token,
            'facebook_pages': self.page_access_tokens,
            'instagram_accounts': self.instagram_accounts,
            'timestamp': __import__('time').time()
        }

        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)

        print(f"✅ Page access tokens saved to {filename}")

    def print_page_access_tokens(self):
        """
        Print all extracted page access tokens in a clear format.
        """
        print("\n📋 FACEBOOK PAGE ACCESS TOKENS:")
        print("=" * 50)

        if not self.page_access_tokens:
            print("No Facebook pages found with access tokens.")
            return

        for page_id, page_data in self.page_access_tokens.items():
            print(f"\n📄 Page: {page_data['page_name']}")
            print(f"   Page ID: {page_id}")
            print(f"   Page Access Token: {page_data['page_access_token'][:30]}... (truncated)")

            if page_data['instagram_business_account']:
                insta_id = page_data['instagram_business_account']['id']
                print(f"   📸 Connected Instagram Account: {insta_id}")

        print(f"\n📊 Total Facebook Pages: {len(self.page_access_tokens)}")

        if self.instagram_accounts:
            print(f"\n📸 INSTAGRAM ACCOUNTS WITH PAGE TOKENS:")
            print("=" * 50)

            for i, insta_account in enumerate(self.instagram_accounts, 1):
                print(f"\n{i}. Instagram Account ID: {insta_account['id']}")
                print(f"   Connected to Page: {insta_account['page_name']} (ID: {insta_account['page_id']})")
                print(f"   Page Access Token: {insta_account['page_access_token'][:30]}... (truncated)")

            print(f"\n📊 Total Instagram Accounts: {len(self.instagram_accounts)}")

def main():
    """
    Main function focused on extracting page access tokens.
    """
    print("🔑 PAGE ACCESS TOKEN EXTRACTOR")
    print("=" * 50)
    print("This script extracts Facebook and Instagram page access tokens")
    print("Focus: Getting PAGE access tokens (not user or app tokens)")
    print()

    try:
        # Initialize extractor
        extractor = PageAccessTokenExtractor()
        print("✅ Page access token extractor initialized")

        # Get auth URL
        auth_url = extractor.get_auth_url()
        print(f"\n🔗 Authorization URL: {auth_url}")

        # Open in browser
        try:
            webbrowser.open(auth_url)
            print("🌐 Opening authorization URL in your browser...")
        except:
            print("📝 Please copy and paste the URL above into your browser")

        # Get auth code from user
        auth_code_input = input("\n📥 After authorizing, paste the full redirect URL here: ").strip()

        if not auth_code_input:
            print("❌ No URL provided")
            return

        # Extract code
        try:
            parsed_url = urlparse(auth_code_input)
            code = parse_qs(parsed_url.query).get('code', [None])[0]
            if not code:
                code = auth_code_input  # Maybe user pasted just the code
        except:
            code = auth_code_input

        print(f"\n🔑 Using authorization code: {code[:20]}... (truncated)")

        # Exchange for user token
        print("\n🔄 Getting user access token...")
        user_token = extractor.exchange_code_for_user_token(code)
        print(f"✅ User access token obtained: {user_token[:20]}... (truncated)")

        # Extract ALL page access tokens
        print("\n🚀 Extracting page access tokens...")
        page_tokens = extractor.get_all_page_access_tokens()

        # Display results
        extractor.print_page_access_tokens()

        # Save to file
        extractor.save_page_tokens_to_file()

        # Show usage examples
        print(f"\n💡 HOW TO USE THESE PAGE ACCESS TOKENS:")
        print("=" * 50)

        if page_tokens:
            # Show Facebook page usage example
            first_page_id = next(iter(page_tokens.keys()))
            first_page_token = page_tokens[first_page_id]['page_access_token']

            print(f"\n📘 Facebook Page API Example:")
            print(f"Page ID: {first_page_id}")
            print(f"Page Access Token: {first_page_token[:30]}...")
            print()
            print("Usage:")
            print(f"  POST to Facebook Page:")
            print(f"  https://graph.facebook.com/{first_page_id}/feed")
            print(f"  ?message=Hello&access_token={first_page_token[:15]}...")
            print()

        if extractor.instagram_accounts:
            first_insta = extractor.instagram_accounts[0]
            insta_id = first_insta['id']
            page_token = first_insta['page_access_token']

            print(f"📸 Instagram API Example:")
            print(f"Instagram Account ID: {insta_id}")
            print(f"Page Access Token: {page_token[:30]}...")
            print()
            print("Usage:")
            print(f"  Get Instagram User Info:")
            print(f"  https://graph.facebook.com/{insta_id}")
            print(f"  ?fields=id,username,biography&access_token={page_token[:15]}...")
            print()
            print(f"  Post to Instagram:")
            print(f"  https://graph.facebook.com/{insta_id}/media")
            print(f"  ?image_url=URL&caption=Hello&access_token={page_token[:15]}...")

        print(f"\n✅ SUCCESS: Extracted {len(page_tokens)} Facebook page tokens")
        if extractor.instagram_accounts:
            print(f"✅ SUCCESS: Extracted {len(extractor.instagram_accounts)} Instagram page tokens")

        print(f"\n📁 All tokens saved to 'page_access_tokens.json'")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n📝 Make sure your .env file has correct credentials:")
        print("FB_CLIENT_ID=your_facebook_client_id")
        print("FB_CLIENT_SECRET=your_facebook_client_secret")
        print("FB_REDIRECT_URI=http://localhost:5000/auth/facebook/callback")

if __name__ == "__main__":
    main()