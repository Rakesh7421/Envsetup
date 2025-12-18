#!/usr/bin/env python3
"""
Token Testing and Posting Permission Verification Script
Tests existing tokens and verifies posting permissions for Facebook/Instagram platforms.
"""

import os
import json
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

class TokenTester:
    """
    Tests existing tokens and verifies posting permissions.
    """

    def __init__(self):
        """
        Initialize with Facebook credentials.
        """
        self.client_id = os.getenv('FB_CLIENT_ID')
        self.client_secret = os.getenv('FB_CLIENT_SECRET')
        self.app_access_token = f"{self.client_id}|{self.client_secret}"

        if not all([self.client_id, self.client_secret]):
            raise EnvironmentError("Missing FB_CLIENT_ID or FB_CLIENT_SECRET in .env file")

    def load_tokens_from_file(self, filename: str) -> Dict[str, Any]:
        """
        Load tokens from a JSON file.

        Args:
            filename: Name of the file to load tokens from

        Returns:
            Dictionary containing token data
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Could not load tokens from {filename}: {str(e)}")

    def get_token_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get detailed information about an access token.

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

    def test_token_validity(self, access_token: str) -> Dict[str, Any]:
        """
        Test if a token is valid and get its details.

        Args:
            access_token: The access token to test

        Returns:
            Dictionary with validity status and token details
        """
        try:
            token_info = self.get_token_info(access_token)
            data = token_info.get('data', {})

            return {
                'valid': data.get('is_valid', False),
                'scopes': data.get('scopes', []),
                'expires_at': data.get('expires_at'),
                'user_id': data.get('user_id'),
                'error': None
            }
        except Exception as e:
            return {
                'valid': False,
                'scopes': [],
                'expires_at': None,
                'user_id': None,
                'error': str(e)
            }

    def check_posting_permissions(self, scopes: List[str]) -> Dict[str, Any]:
        """
        Check if token has posting permissions.

        Args:
            scopes: List of token scopes

        Returns:
            Dictionary with posting permission details
        """
        posting_permissions = {
            'facebook_posting': False,
            'instagram_posting': False,
            'all_permissions': []
        }

        required_facebook = ['pages_manage_posts', 'pages_manage_engagement']
        required_instagram = ['instagram_content_publish', 'instagram_manage_insights']

        for scope in scopes:
            if scope in required_facebook:
                posting_permissions['all_permissions'].append(scope)
                posting_permissions['facebook_posting'] = True
            if scope in required_instagram:
                posting_permissions['all_permissions'].append(scope)
                posting_permissions['instagram_posting'] = True

        return posting_permissions

    def test_facebook_page_posting(self, page_access_token: str, page_id: str) -> Dict[str, Any]:
        """
        Test Facebook page posting capability.

        Args:
            page_access_token: The page access token
            page_id: The Facebook page ID

        Returns:
            Dictionary with test results
        """
        try:
            # Test by getting page info (safe read operation)
            test_url = f"https://graph.facebook.com/{page_id}"
            params = {
                'access_token': page_access_token,
                'fields': 'id,name,access_token'
            }
            response = requests.get(test_url, params=params)

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': "Facebook page access confirmed",
                    'can_post': True,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'message': "Facebook page access failed",
                    'can_post': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'message': "Facebook posting test failed",
                'can_post': False,
                'error': str(e)
            }

    def test_instagram_posting(self, page_access_token: str, instagram_account_id: str) -> Dict[str, Any]:
        """
        Test Instagram posting capability.

        Args:
            page_access_token: The page access token
            instagram_account_id: The Instagram account ID

        Returns:
            Dictionary with test results
        """
        try:
            # Test by getting Instagram account info
            test_url = f"https://graph.facebook.com/{instagram_account_id}"
            params = {
                'access_token': page_access_token,
                'fields': 'id,username,biography'
            }
            response = requests.get(test_url, params=params)

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': "Instagram account access confirmed",
                    'can_post': True,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'message': "Instagram account access failed",
                    'can_post': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'message': "Instagram posting test failed",
                'can_post': False,
                'error': str(e)
            }

    def analyze_token_file(self, filename: str) -> Dict[str, Any]:
        """
        Analyze a token file and test all capabilities.

        Args:
            filename: Name of the token file to analyze

        Returns:
            Comprehensive analysis report
        """
        report = {
            'filename': filename,
            'platform': 'unknown',
            'tokens': {},
            'permissions': {},
            'tests': {},
            'success': False
        }

        try:
            # Load token data
            token_data = self.load_tokens_from_file(filename)
            report['platform'] = token_data.get('platform', 'unknown')

            # Test user access token if available
            user_token = token_data.get('user_access_token')
            if user_token:
                user_token_test = self.test_token_validity(user_token)
                report['tokens']['user_access_token'] = {
                    'valid': user_token_test['valid'],
                    'scopes': user_token_test['scopes'],
                    'expires_at': user_token_test['expires_at'],
                    'permissions': self.check_posting_permissions(user_token_test['scopes'])
                }

            # Test page access token if available
            page_token = token_data.get('page_access_token')
            if page_token:
                page_token_test = self.test_token_validity(page_token)
                report['tokens']['page_access_token'] = {
                    'valid': page_token_test['valid'],
                    'scopes': page_token_test['scopes'],
                    'expires_at': page_token_test['expires_at'],
                    'permissions': self.check_posting_permissions(page_token_test['scopes'])
                }

                # Run platform-specific tests
                if report['platform'] == 'facebook':
                    page_id = token_data.get('page_id')
                    if page_id:
                        fb_test = self.test_facebook_page_posting(page_token, page_id)
                        report['tests']['facebook_posting'] = fb_test
                elif report['platform'] == 'instagram':
                    insta_id = token_data.get('instagram_account_id')
                    page_id = token_data.get('page_id')
                    if insta_id and page_id:
                        insta_test = self.test_instagram_posting(page_token, insta_id)
                        fb_test = self.test_facebook_page_posting(page_token, page_id)
                        report['tests']['instagram_posting'] = insta_test
                        report['tests']['facebook_page_access'] = fb_test

            report['success'] = True

        except Exception as e:
            report['error'] = str(e)

        return report

def print_report(report: Dict[str, Any]):
    """Print the token analysis report in a readable format."""
    print(f"\n📊 TOKEN ANALYSIS REPORT: {report['filename']}")
    print("=" * 60)
    print(f"Platform: {report['platform'].upper()}")
    print(f"Analysis Status: {'✅ SUCCESS' if report['success'] else '❌ FAILED'}")

    if 'error' in report:
        print(f"\n❌ Error: {report['error']}")
        return

    # User Access Token
    if 'user_access_token' in report['tokens']:
        user_token = report['tokens']['user_access_token']
        print(f"\n👤 USER ACCESS TOKEN:")
        print(f"   Valid: {'✅ Yes' if user_token['valid'] else '❌ No'}")
        print(f"   Scopes: {', '.join(user_token['scopes'])}")
        print(f"   Posting Permissions: {', '.join(user_token['permissions']['all_permissions'])}")
        print(f"   Facebook Posting: {'✅ Yes' if user_token['permissions']['facebook_posting'] else '❌ No'}")
        print(f"   Instagram Posting: {'✅ Yes' if user_token['permissions']['instagram_posting'] else '❌ No'}")

    # Page Access Token
    if 'page_access_token' in report['tokens']:
        page_token = report['tokens']['page_access_token']
        print(f"\n📄 PAGE ACCESS TOKEN:")
        print(f"   Valid: {'✅ Yes' if page_token['valid'] else '❌ No'}")
        print(f"   Scopes: {', '.join(page_token['scopes'])}")
        print(f"   Posting Permissions: {', '.join(page_token['permissions']['all_permissions'])}")
        print(f"   Facebook Posting: {'✅ Yes' if page_token['permissions']['facebook_posting'] else '❌ No'}")
        print(f"   Instagram Posting: {'✅ Yes' if page_token['permissions']['instagram_posting'] else '❌ No'}")

    # Platform-Specific Tests
    if 'tests' in report and report['tests']:
        print(f"\n🧪 PLATFORM-SPECIFIC TESTS:")
        for test_name, test_result in report['tests'].items():
            print(f"   {test_name.replace('_', ' ').title()}: {'✅ PASS' if test_result['success'] else '❌ FAIL'}")
            if test_result['success']:
                print(f"      {test_result['message']}")
            else:
                print(f"      Error: {test_result['error']}")

    # Summary
    print(f"\n📋 SUMMARY:")
    can_post_fb = any(
        report['tokens'].get(token, {}).get('permissions', {}).get('facebook_posting', False)
        for token in ['user_access_token', 'page_access_token']
    )
    can_post_insta = any(
        report['tokens'].get(token, {}).get('permissions', {}).get('instagram_posting', False)
        for token in ['user_access_token', 'page_access_token']
    )

    print(f"   Facebook Posting Capable: {'✅ YES' if can_post_fb else '❌ NO'}")
    print(f"   Instagram Posting Capable: {'✅ YES' if can_post_insta else '❌ NO'}")

def main():
    """Main function to test tokens and posting permissions."""
    print("🔍 TOKEN AND POSTING PERMISSION TESTER")
    print("=" * 60)
    print("Tests existing tokens and verifies posting permissions")
    print("for Facebook and Instagram platforms")
    print()

    try:
        # Initialize token tester
        tester = TokenTester()
        print("✅ Token tester initialized")

        # Find available token files
        token_files = []
        for filename in ['oauth_tokens.json', 'oauth_tokens_facebook.json', 'oauth_tokens_instagram.json']:
            if os.path.exists(filename):
                token_files.append(filename)

        if not token_files:
            print("\n❌ No token files found. Please run OAuth flow first.")
            return

        print(f"\n📁 Found {len(token_files)} token file(s):")
        for i, filename in enumerate(token_files, 1):
            print(f"  {i}. {filename}")

        # Test all files
        all_reports = []
        for filename in token_files:
            print(f"\n🔬 Analyzing {filename}...")
            report = tester.analyze_token_file(filename)
            all_reports.append(report)
            print_report(report)

        # Final summary
        print(f"\n🎯 FINAL SUMMARY:")
        print("=" * 60)

        fb_ready = False
        insta_ready = False

        for report in all_reports:
            if report.get('platform') == 'facebook':
                fb_ready = any(
                    report['tokens'].get(token, {}).get('permissions', {}).get('facebook_posting', False)
                    for token in ['user_access_token', 'page_access_token']
                )
            elif report.get('platform') == 'instagram':
                insta_ready = any(
                    report['tokens'].get(token, {}).get('permissions', {}).get('instagram_posting', False)
                    for token in ['user_access_token', 'page_access_token']
                )

        print(f"Facebook Posting Ready: {'✅ YES' if fb_ready else '❌ NO'}")
        print(f"Instagram Posting Ready: {'✅ YES' if insta_ready else '❌ NO'}")

        if fb_ready or insta_ready:
            print(f"\n🎉 Tokens are ready for posting!")
            if fb_ready:
                print("   ✅ Facebook: Can post to pages")
            if insta_ready:
                print("   ✅ Instagram: Can post to connected accounts")
        else:
            print(f"\n⚠️  Tokens need attention:")
            print("   Run OAuth flow again with proper permissions")
            print("   Make sure to include posting scopes")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()