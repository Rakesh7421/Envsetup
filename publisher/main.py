#!/usr/bin/env python3
"""
Main Publisher Application
Integrates content fetching, management, and posting to social media platforms.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from poster import PlatformPoster
from content_server import ContentServer
from fetch_content import ContentFetcher

class PublisherApp:
    """
    Main publisher application that orchestrates the publishing workflow.
    """

    def __init__(self):
        """
        Initialize the publisher application with all components.
        """
        self.poster = PlatformPoster()
        self.content_server = ContentServer()
        self.rss_fetcher = ContentFetcher()

        # Default RSS feeds to monitor
        self.default_rss_feeds = [
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://www.theguardian.com/world/rss'
        ]

    def load_tokens(self, platform: str) -> Optional[Dict[str, Any]]:
        """
        Load OAuth tokens for the specified platform with fallback mechanism.

        Args:
            platform: Platform name ('facebook' or 'instagram')

        Returns:
            Dictionary with token data, or None if not found
        """
        token_files = {
            'facebook': 'oauth_tokens_facebook.json',
            'instagram': 'oauth_tokens_instagram.json'
        }

        filename = token_files.get(platform.lower())
        if not filename:
            return None

        try:
            if os.path.exists(filename):
                tokens = self.poster.load_tokens_from_file(filename)

                # Check if tokens are valid (not null/empty)
                if self._are_tokens_valid(tokens, platform):
                    return tokens
                else:
                    print(f"⚠️  Token file {filename} exists but contains invalid/missing tokens")
                    print(f"   Attempting to get valid tokens from OAuth system...")

                    # Try to get valid tokens from OAuth system
                    valid_tokens = self._get_valid_tokens_from_oauth(platform)
                    if valid_tokens:
                        return valid_tokens
                    else:
                        print(f"❌ Could not obtain valid tokens for {platform}")
                        return None
            else:
                print(f"⚠️  Token file {filename} not found")
                print(f"   Attempting to get tokens from OAuth system...")

                # Try to get tokens from OAuth system
                valid_tokens = self._get_valid_tokens_from_oauth(platform)
                if valid_tokens:
                    return valid_tokens
                else:
                    print(f"❌ Could not obtain tokens for {platform}")
                    return None
        except Exception as e:
            print(f"❌ Could not load tokens: {str(e)}")
            return None

    def _are_tokens_valid(self, tokens: Dict[str, Any], platform: str) -> bool:
        """
        Check if tokens contain valid data for the specified platform.

        Args:
            tokens: Token dictionary to validate
            platform: Platform name ('facebook' or 'instagram')

        Returns:
            True if tokens are valid, False otherwise
        """
        if not tokens:
            return False

        # Check for required fields based on platform
        if platform.lower() == 'facebook':
            # For Facebook, we need either page_access_token + page_id OR user_access_token
            has_page_tokens = bool(tokens.get('page_access_token')) and bool(tokens.get('page_id'))
            has_user_token = bool(tokens.get('user_access_token'))

            return has_page_tokens or has_user_token

        elif platform.lower() == 'instagram':
            # For Instagram, we need either page_access_token + instagram_account_id OR user_access_token
            has_insta_tokens = bool(tokens.get('page_access_token')) and bool(tokens.get('instagram_account_id'))
            has_user_token = bool(tokens.get('user_access_token'))

            return has_insta_tokens or has_user_token

        return False

    def _get_valid_tokens_from_oauth(self, platform: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to get valid tokens from the OAuth system.

        Args:
            platform: Platform name ('facebook' or 'instagram')

        Returns:
            Dictionary with valid token data, or None if not available
        """
        try:
            # Import the OAuth token extractor
            import sys
            sys.path.append('Oauth')
            from get_page_access_tokens import PageAccessTokenExtractor # type: ignore

            # Try to initialize the extractor
            try:
                extractor = PageAccessTokenExtractor()

                # Get all page access tokens
                page_tokens = extractor.get_all_page_access_tokens()

                if not page_tokens:
                    print(f"ℹ️  No page access tokens available from OAuth system")
                    return None

                # Create token data based on platform
                if platform.lower() == 'facebook':
                    # Get the first Facebook page
                    first_page_id = next(iter(page_tokens.keys()))
                    first_page_data = page_tokens[first_page_id]

                    return {
                        'user_access_token': extractor.user_access_token,
                        'page_access_token': first_page_data['page_access_token'],
                        'page_id': first_page_id,
                        'platform': 'facebook',
                        'timestamp': __import__('time').time()
                    }

                elif platform.lower() == 'instagram':
                    # Get the first Instagram account
                    instagram_accounts = extractor.get_instagram_page_tokens()
                    if instagram_accounts:
                        first_insta = instagram_accounts[0]

                        return {
                            'user_access_token': extractor.user_access_token,
                            'page_access_token': first_insta['page_access_token'],
                            'instagram_account_id': first_insta['id'],
                            'page_id': first_insta['page_id'],
                            'platform': 'instagram',
                            'timestamp': __import__('time').time()
                        }
                    else:
                        print(f"ℹ️  No Instagram accounts found in OAuth system")
                        return None

            except Exception as e:
                print(f"⚠️  Could not initialize OAuth extractor: {str(e)}")
                print(f"   Make sure .env file has proper credentials")
                return None

        except Exception as e:
            print(f"⚠️  Could not import OAuth extractor: {str(e)}")
            return None

    def fetch_and_process_content(self, rss_feeds: Optional[List[str]] = None, max_items: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch content from RSS feeds and process it for publishing.

        Args:
            rss_feeds: List of RSS feed URLs (uses defaults if None)
            max_items: Maximum items to fetch from each feed

        Returns:
            List of processed content items ready for publishing
        """
        feeds_to_use = rss_feeds or self.default_rss_feeds

        print(f"📡 Fetching content from {len(feeds_to_use)} RSS feeds...")
        all_content = []

        for feed_url in feeds_to_use:
            try:
                print(f"🌐 Processing: {feed_url}")
                # Fetch content with media requirement for Instagram compatibility
                feed_items = self.rss_fetcher.fetch_rss_feed(feed_url, max_items, require_media=True)

                for item in feed_items:
                    # Create content item
                    content = self.content_server.create_content(
                        title=item['title'],
                        body=item['content'],
                        author=item['author'],
                        tags=['rss', item['domain']]
                    )

                    # Add source information
                    content['source_url'] = item['url']
                    content['source_domain'] = item['domain']

                    all_content.append(content)

                print(f"✅ Retrieved {len(feed_items)} items from {feed_url}")

            except Exception as e:
                print(f"⚠️  Could not process {feed_url}: {str(e)}")

        print(f"📚 Total content items ready: {len(all_content)}")
        return all_content

    def publish_content_to_platform(self, content: Dict[str, Any], platform: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a content item to the specified platform.

        Args:
            content: Content dictionary to publish
            platform: Target platform ('facebook' or 'instagram')
            tokens: OAuth tokens for the platform

        Returns:
            Dictionary with publishing results
        """
        print(f"📤 Publishing '{content['title']}' to {platform}...")

        # Check for redundancy
        redundancy_check = self.content_server.check_content_redundancy(content)
        if redundancy_check['is_redundant']:
            print(f"⚠️  Content '{content['title']}' appears to be redundant, skipping...")
            # Create a post_result for consistency with reference to already posted content
            post_result = {
                'success': False,
                'message': 'Content is redundant',
                'error': 'redundant_content',
                'already_posted_reference': redundancy_check['reference'],
                'platform': redundancy_check['platform'],
                'timestamp': redundancy_check['timestamp']
            }
            # Update content status
            updated_content = self.content_server.update_content_status(
                content=content,
                status='skipped',
                platform=platform,
                post_result=post_result
            )
            # Log the skipped content
            self.content_server.log_content_post(content, platform, post_result)
            return {
                'content': updated_content,
                'post_result': post_result,
                'platform_content': None
            }

        # For Instagram, check if content has media (image/video)
        if platform.lower() == 'instagram':
            # Create an rss_item structure that the fetcher expects
            rss_item = {
                'title': content['title'],
                'content': content['body'],
                'url': content.get('source_url', ''),
                'domain': content.get('source_domain', 'unknown'),
                'raw_entry': {}
            }
            platform_content = self.rss_fetcher.get_content_for_publishing(rss_item, platform)

            # Check if we have an image URL for Instagram
            if not platform_content.get('image_url'):
                print(f"⚠️  Content '{content['title']}' has no media for Instagram, skipping...")
                # Create a post_result for consistency
                post_result = {
                    'success': False,
                    'message': 'Content has no media for Instagram',
                    'error': 'no_media_for_instagram'
                }
                # Update content status
                updated_content = self.content_server.update_content_status(
                    content=content,
                    status='skipped',
                    platform=platform,
                    post_result=post_result
                )
                # Log the skipped content
                self.content_server.log_content_post(content, platform, post_result)
                return {
                    'content': updated_content,
                    'post_result': post_result,
                    'platform_content': platform_content
                }

        # Prepare content for the platform
        # Create an rss_item structure that the fetcher expects
        rss_item = {
            'title': content['title'],
            'content': content['body'],
            'url': content.get('source_url', ''),
            'domain': content.get('source_domain', 'unknown'),
            'raw_entry': {}
        }
        platform_content = self.rss_fetcher.get_content_for_publishing(rss_item, platform)

        # Post to platform
        post_result = self.poster.post_to_platform(
            platform=platform,
            tokens=tokens,
            content=platform_content['content'],
            image_url=platform_content.get('image_url')
        )

        # Update content status
        if post_result['success']:
            updated_content = self.content_server.update_content_status(
                content=content,
                status='published',
                platform=platform,
                post_result=post_result
            )
            print(f"✅ Successfully published to {platform}!")
        else:
            updated_content = self.content_server.update_content_status(
                content=content,
                status='failed',
                platform=platform,
                post_result=post_result
            )
            print(f"❌ Failed to publish to {platform}: {post_result['error']}")

        # Log the post to CSV
        self.content_server.log_content_post(content, platform, post_result)

        return {
            'content': updated_content,
            'post_result': post_result,
            'platform_content': platform_content
        }

    def publish_to_all_platforms(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish content to all available platforms.

        Args:
            content: Content dictionary to publish

        Returns:
            Dictionary with results for all platforms
        """
        results = {
            'content': content,
            'platforms': {}
        }

        # Try Facebook
        fb_tokens = self.load_tokens('facebook')
        if fb_tokens:
            fb_result = self.publish_content_to_platform(content, 'facebook', fb_tokens)
            results['platforms']['facebook'] = fb_result

        # Try Instagram
        insta_tokens = self.load_tokens('instagram')
        if insta_tokens:
            insta_result = self.publish_content_to_platform(content, 'instagram', insta_tokens)
            results['platforms']['instagram'] = insta_result

        return results

    def run_publishing_workflow(self, rss_feeds: Optional[List[str]] = None, max_items: int = 2) -> List[Dict[str, Any]]:
        """
        Run the complete publishing workflow: fetch, process, and publish content.

        Args:
            rss_feeds: List of RSS feed URLs (uses defaults if None)
            max_items: Maximum items to process from each feed

        Returns:
            List of publishing results
        """
        print("🚀 Starting publishing workflow...")
        print("=" * 50)

        # Step 1: Fetch and process content
        content_items = self.fetch_and_process_content(rss_feeds, max_items)

        if not content_items:
            print("❌ No content items to publish")
            return []

        # Step 2: Publish each content item
        all_results = []

        for i, content in enumerate(content_items, 1):
            print(f"\n📄 Processing content item {i}/{len(content_items)}:")
            print(f"   Title: {content['title']}")
            print(f"   Source: {content.get('source_domain', 'Unknown')}")

            # Publish to all platforms
            publish_results = self.publish_to_all_platforms(content)
            all_results.append(publish_results)

            # Save the content with updated status
            try:
                filename = f"published_{content['source_domain']}_{i}.json"
                self.content_server.save_content(publish_results['content'], filename)
                print(f"💾 Saved published content to {filename}")
            except Exception as e:
                print(f"⚠️  Could not save content: {str(e)}")

            # Add delay between posts to avoid rate limiting
            if i < len(content_items):
                print("⏳ Waiting 30 seconds before next post...")
                time.sleep(30)

        print(f"\n🎉 Publishing workflow completed!")
        print(f"   Processed {len(content_items)} content items")
        print(f"   Generated {len(all_results)} publishing results")

        return all_results

    def manual_publishing_mode(self):
        """
        Interactive mode for manual content creation and publishing.
        """
        print("📝 Manual Publishing Mode")
        print("=" * 40)

        # Create content
        print("\n📚 Create new content:")
        title = input("   Title: ").strip()
        body = input("   Content (press Enter, then type/paste content, Ctrl+D to finish):\n").strip()

        content = self.content_server.create_content(
            title=title,
            body=body,
            author=input("   Author (default: system): ").strip() or 'system'
        )

        # Choose platforms
        platforms = []
        print("\n📱 Choose platforms to publish to:")
        print("   1. Facebook")
        print("   2. Instagram")
        print("   3. Both")

        choice = input("   Enter choice (1/2/3): ").strip()

        if choice == '1':
            platforms = ['facebook']
        elif choice == '2':
            platforms = ['instagram']
        elif choice == '3':
            platforms = ['facebook', 'instagram']
        else:
            print("❌ Invalid choice")
            return

        # Publish to selected platforms
        for platform in platforms:
            tokens = self.load_tokens(platform)
            if tokens:
                result = self.publish_content_to_platform(content, platform, tokens)
                print(f"\n{platform.capitalize()} Result: {result['post_result']['message']}")
            else:
                print(f"⚠️  No tokens available for {platform}")

    def check_token_status(self):
        """
        Check the status of available OAuth tokens.
        """
        print("🔑 Token Status Check")
        print("=" * 30)

        platforms = ['facebook', 'instagram']
        for platform in platforms:
            tokens = self.load_tokens(platform)
            if tokens:
                print(f"\n{platform.capitalize()} Tokens:")
                print(f"   User Access Token: {'✅ Available' if tokens.get('user_access_token') else '❌ Missing'}")
                print(f"   Page Access Token: {'✅ Available' if tokens.get('page_access_token') else '❌ Missing'}")
                print(f"   Account ID: {tokens.get('instagram_account_id', tokens.get('page_id', 'N/A'))}")
            else:
                print(f"\n{platform.capitalize()}: ❌ No tokens available")

def main():
    """Main entry point for the publisher application."""
    print("📢 Social Media Publisher")
    print("=" * 40)
    print("Automated content publishing system")
    print("with RSS feed integration and redundancy prevention")
    print()

    try:
        publisher = PublisherApp()
        print("✅ Publisher application initialized")

        # Automatically run the publishing workflow
        print("\n🚀 Running automated publishing workflow...")
        results = publisher.run_publishing_workflow(max_items=1)  # Limit to 1 item for demo

        print(f"\n📊 Summary:")
        print(f"   Processed {len(results)} content items")

        for i, result in enumerate(results, 1):
            print(f"\n   Item {i}: {result['content']['title']}")
            for platform, platform_result in result['platforms'].items():
                status = "✅ Published" if platform_result['post_result'].get('success', False) else "❌ Failed"
                print(f"      {platform.capitalize()}: {status}")

        print("\n🎉 Publishing workflow completed successfully!")

    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()