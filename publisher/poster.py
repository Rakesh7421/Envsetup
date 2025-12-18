#!/usr/bin/env python3
"""
Publisher Poster Module
Handles posting content to various social media platforms using OAuth tokens.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import csv

class PlatformPoster:
    """
    Handles posting content to Facebook and Instagram platforms.
    """

    def __init__(self):
        """
        Initialize the poster with required credentials.
        """
        self.client_id = os.getenv('FB_CLIENT_ID', '')
        self.client_secret = os.getenv('FB_CLIENT_SECRET', '')
        self.app_access_token = f"{self.client_id}|{self.client_secret}" if self.client_id and self.client_secret else None

        # Don't require environment variables since we'll use token files
        # if not all([self.client_id, self.client_secret]):
        #     raise EnvironmentError("Missing FB_CLIENT_ID or FB_CLIENT_SECRET in .env file")

    def _get_page_info_from_user_token(self, user_access_token: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to get page information from a user access token.

        Args:
            user_access_token: User access token to inspect

        Returns:
            Dictionary with page info if found, None otherwise
        """
        try:
            if not self.app_access_token:
                return None

            # Try to get user's pages
            pages_url = f"https://graph.facebook.com/me/accounts"
            params = {
                'access_token': user_access_token,
                'fields': 'id,name,access_token'
            }

            response = requests.get(pages_url, params=params)
            if response.status_code == 200:
                pages_data = response.json()
                if 'data' in pages_data and pages_data['data']:
                    # Return the first page found
                    first_page = pages_data['data'][0]
                    return {
                        'page_id': first_page['id'],
                        'page_name': first_page.get('name', 'Unknown'),
                        'page_access_token': first_page.get('access_token')
                    }

            return None

        except Exception as e:
            print(f"⚠️  Could not get page info from user token: {str(e)}")
            return None

    def _get_instagram_info_from_user_token(self, user_access_token: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to get Instagram account information from a user access token.

        Args:
            user_access_token: User access token to inspect

        Returns:
            Dictionary with Instagram info if found, None otherwise
        """
        try:
            if not self.app_access_token:
                return None

            # First get user's pages
            pages_url = f"https://graph.facebook.com/me/accounts"
            params = {
                'access_token': user_access_token,
                'fields': 'id,name,access_token,instagram_business_account'
            }

            response = requests.get(pages_url, params=params)
            if response.status_code == 200:
                pages_data = response.json()
                if 'data' in pages_data and pages_data['data']:
                    # Look for pages with Instagram accounts
                    for page in pages_data['data']:
                        if 'instagram_business_account' in page:
                            insta_account = page['instagram_business_account']
                            return {
                                'instagram_account_id': insta_account['id'],
                                'page_id': page['id'],
                                'page_name': page.get('name', 'Unknown'),
                                'page_access_token': page.get('access_token')
                            }

            return None

        except Exception as e:
            print(f"⚠️  Could not get Instagram info from user token: {str(e)}")
            return None

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

    def post_to_facebook_page(self, page_access_token: str, page_id: str, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Post content to a Facebook page.

        Args:
            page_access_token: The page access token
            page_id: The Facebook page ID
            content: The text content to post
            image_url: Optional image URL to include in the post

        Returns:
            Dictionary with posting results
        """
        try:
            post_url = f"https://graph.facebook.com/{page_id}/feed"
            params = {
                'access_token': page_access_token,
                'message': content
            }

            if image_url:
                params['link'] = image_url

            response = requests.post(post_url, params=params)

            if response.status_code == 200:
                post_data = response.json()
                return {
                    'success': True,
                    'post_id': post_data.get('id'),
                    'message': "Facebook post created successfully",
                    'post_url': f"https://facebook.com/{post_data.get('id')}",
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'post_id': None,
                    'message': "Facebook post failed",
                    'post_url': None,
                    'error': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'post_id': None,
                'message': "Facebook posting error",
                'post_url': None,
                'error': str(e)
            }

    def post_to_instagram(self, page_access_token: str, instagram_account_id: str, image_url: str, caption: str) -> Dict[str, Any]:
        """
        Post content to Instagram.

        Args:
            page_access_token: The page access token
            instagram_account_id: The Instagram account ID
            image_url: URL of the image to post
            caption: Caption for the Instagram post

        Returns:
            Dictionary with posting results
        """
        try:
            # Step 1: Create container
            container_url = f"https://graph.facebook.com/{instagram_account_id}/media"
            container_params = {
                'access_token': page_access_token,
                'image_url': image_url,
                'caption': caption
            }

            container_response = requests.post(container_url, params=container_params)

            if container_response.status_code != 200:
                return {
                    'success': False,
                    'container_id': None,
                    'message': "Failed to create Instagram container",
                    'error': container_response.text
                }

            container_data = container_response.json()
            container_id = container_data.get('id')

            # Step 2: Publish the container
            publish_url = f"https://graph.facebook.com/{instagram_account_id}/media_publish"
            publish_params = {
                'access_token': page_access_token,
                'creation_id': container_id
            }

            publish_response = requests.post(publish_url, params=publish_params)

            if publish_response.status_code == 200:
                return {
                    'success': True,
                    'container_id': container_id,
                    'message': "Instagram post published successfully",
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'container_id': container_id,
                    'message': "Failed to publish Instagram post",
                    'error': publish_response.text
                }

        except Exception as e:
            return {
                'success': False,
                'container_id': None,
                'message': "Instagram posting error",
                'error': str(e)
            }

    def post_to_platform(self, platform: str, tokens: Dict[str, Any], content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Post content to the specified platform.

        Args:
            platform: Either 'facebook' or 'instagram'
            tokens: Dictionary containing token data
            content: The content to post
            image_url: Optional image URL

        Returns:
            Dictionary with posting results
        """
        if platform.lower() == 'facebook':
            page_access_token = tokens.get('page_access_token')
            page_id = tokens.get('page_id')
            user_access_token = tokens.get('user_access_token')

            if not all([page_access_token, page_id]):
                # NEW: Fallback to user access token if page access token is missing
                # but we have page_id and user_access_token with proper permissions
                if page_id and user_access_token:
                    print(f"ℹ️  Using user access token for Facebook posting (page access token not available)")
                    return self.post_to_facebook_page(str(user_access_token), str(page_id), content, image_url)
                elif user_access_token:
                    # If we have user access token but no page_id, try to get page_id from token
                    print(f"ℹ️  Attempting to get page_id from user access token")
                    page_info = self._get_page_info_from_user_token(user_access_token)
                    if page_info and page_info.get('page_id'):
                        print(f"ℹ️  Found page_id {page_info['page_id']} from user token")
                        return self.post_to_facebook_page(str(user_access_token), str(page_info['page_id']), content, image_url)
                    else:
                        print(f"⚠️  Could not determine page_id from user access token")
                else:
                    print(f"❌ No valid tokens available for Facebook posting")
                return {
                    'success': False,
                    'message': "Missing required Facebook token data",
                    'error': "page_access_token or page_id not found in tokens"
                }

            return self.post_to_facebook_page(str(page_access_token), str(page_id), content, image_url)

        elif platform.lower() == 'instagram':
            page_access_token = tokens.get('page_access_token')
            instagram_account_id = tokens.get('instagram_account_id')
            user_access_token = tokens.get('user_access_token')

            if not all([page_access_token, instagram_account_id]):
                # NEW: Fallback to user access token if page access token is missing
                # but we have instagram_account_id and user_access_token with proper permissions
                if instagram_account_id and user_access_token:
                    print(f"ℹ️  Using user access token for Instagram posting (page access token not available)")
                    if image_url:
                        return self.post_to_instagram(str(user_access_token), str(instagram_account_id), image_url, content)
                    else:
                        return {
                            'success': False,
                            'message': "Image URL is required for Instagram posts",
                            'error': "Instagram posts require an image"
                        }
                elif user_access_token:
                    # If we have user access token but no instagram_account_id, try to get it
                    print(f"ℹ️  Attempting to get Instagram account info from user access token")
                    insta_info = self._get_instagram_info_from_user_token(user_access_token)
                    if insta_info and insta_info.get('instagram_account_id'):
                        print(f"ℹ️  Found Instagram account {insta_info['instagram_account_id']} from user token")
                        if image_url:
                            return self.post_to_instagram(str(user_access_token), str(insta_info['instagram_account_id']), image_url, content)
                        else:
                            return {
                                'success': False,
                                'message': "Image URL is required for Instagram posts",
                                'error': "Instagram posts require an image"
                            }
                    else:
                        print(f"⚠️  Could not determine Instagram account from user access token")
                else:
                    print(f"❌ No valid tokens available for Instagram posting")
                return {
                    'success': False,
                    'message': "Missing required Instagram token data",
                    'error': "page_access_token or instagram_account_id not found in tokens"
                }

            if not image_url:
                return {
                    'success': False,
                    'message': "Image URL is required for Instagram posts",
                    'error': "Instagram posts require an image"
                }

            return self.post_to_instagram(str(page_access_token), str(instagram_account_id), image_url, content)

        else:
            return {
                'success': False,
                'message': f"Unsupported platform: {platform}",
                'error': "Use 'facebook' or 'instagram'"
            }

    def log_post_to_csv(self, post_data: Dict[str, Any], csv_file: str = 'data.csv') -> None:
        """
        Log post information to CSV file to avoid redundancy.

        Args:
            post_data: Dictionary containing post information
            csv_file: Path to CSV file for logging
        """
        try:
            # Check if file exists and has headers
            file_exists = os.path.exists(csv_file)

            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)

                # Write header if file doesn't exist
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'platform', 'content_hash', 'post_id',
                        'success', 'error', 'content_preview'
                    ])

                # Write post data
                writer.writerow([
                    datetime.now().isoformat(),
                    post_data.get('platform', 'unknown'),
                    hash(post_data.get('content', '')) % 1000000,  # Simple hash for content
                    post_data.get('post_id', ''),
                    post_data.get('success', False),
                    post_data.get('error', ''),
                    post_data.get('content', '')[:50] + '...'  # Preview
                ])

        except Exception as e:
            print(f"Warning: Could not log post to CSV: {str(e)}")

    def check_content_redundancy(self, content: str, csv_file: str = 'data.csv') -> bool:
        """
        Check if content has been posted recently to avoid redundancy.

        Args:
            content: The content to check
            csv_file: Path to CSV file with post history

        Returns:
            True if content is redundant, False otherwise
        """
        try:
            if not os.path.exists(csv_file):
                return False

            content_hash = hash(content) % 1000000

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header

                for row in reader:
                    if len(row) >= 3 and int(row[2]) == content_hash:
                        # Content was posted recently
                        return True

            return False

        except Exception as e:
            print(f"Warning: Could not check content redundancy: {str(e)}")
            return False

def main():
    """Test the poster functionality."""
    print("📢 Platform Poster Test")
    print("=" * 40)

    try:
        poster = PlatformPoster()
        print("✅ Platform poster initialized")

        # Test with sample data
        sample_tokens = {
            'page_access_token': 'sample_token',
            'page_id': 'sample_page_id',
            'instagram_account_id': 'sample_insta_id'
        }

        sample_content = "This is a test post from the publisher system!"

        # Test Facebook posting (will fail with sample tokens, but tests the logic)
        print("\n📝 Testing Facebook posting...")
        fb_result = poster.post_to_platform('facebook', sample_tokens, sample_content)
        print(f"Facebook result: {fb_result['message']}")

        # Test Instagram posting (will fail with sample tokens, but tests the logic)
        print("\n📸 Testing Instagram posting...")
        insta_result = poster.post_to_platform('instagram', sample_tokens, sample_content, "https://example.com/image.jpg")
        print(f"Instagram result: {insta_result['message']}")

        # Test redundancy checking
        print("\n🔄 Testing redundancy checking...")
        is_redundant = poster.check_content_redundancy(sample_content)
        print(f"Content is redundant: {is_redundant}")

        # Test logging
        print("\n📋 Testing post logging...")
        poster.log_post_to_csv({
            'platform': 'test',
            'content': sample_content,
            'success': True,
            'error': None
        })
        print("Post logged to CSV")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()