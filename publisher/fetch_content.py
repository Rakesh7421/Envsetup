#!/usr/bin/env python3
"""
Content Fetcher Module
Fetches content from RSS feeds and VisualPing, and prepares it for publishing.
"""

import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import html2text
import requests
from urllib.parse import urlparse
import json

class ContentFetcher:
    """
    Fetches and processes content from RSS feeds and VisualPing.
    """

    def __init__(self, visualping_api_key: Optional[str] = None):
        """
        Initialize the content fetcher.

        Args:
            visualping_api_key: Optional VisualPing API key
        """
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False

        # VisualPing configuration
        self.visualping_api_key = visualping_api_key
        self.visualping_base_url = "https://api.visualping.io/v1"
        self.visualping_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if visualping_api_key:
            self.visualping_headers['Authorization'] = f'Bearer {visualping_api_key}'

    def fetch_rss_feed(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            require_media: If True, only return items that have images/videos (default: True)

        Returns:
            List of parsed feed items with media content
        """
        try:
            # Fetch the RSS feed
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                raise Exception(f"Failed to parse RSS feed: {feed.bozo_exception}")

            # Process feed items
            items = []
            for entry in feed.entries[:max_items]:
                item = self._process_feed_entry(entry)

                # Filter for media-rich content if required
                if require_media:
                    if self._has_media_content(item):
                        items.append(item)
                else:
                    items.append(item)

            return items

        except Exception as e:
            raise Exception(f"Could not fetch RSS feed from {rss_url}: {str(e)}")

    def _process_feed_entry(self, entry: feedparser.FeedParserDict) -> Dict[str, Any]:
        """
        Process a single RSS feed entry into a standardized format.

        Args:
            entry: Raw feedparser entry

        Returns:
            Processed content dictionary
        """
        # Extract basic information
        title = entry.get('title', 'Untitled')
        link = entry.get('link', '')

        # Convert HTML content to markdown
        content_html = ''
        if hasattr(entry, 'content') and entry.content:
            content_html = entry.content[0].get('value', '') if isinstance(entry.content, list) and entry.content else str(entry.content)
        if not content_html and hasattr(entry, 'summary'):
            content_html = entry.summary

        content_text = self.html_converter.handle(str(content_html))

        # Extract publication date
        published = ''
        if hasattr(entry, 'published'):
            published = entry.published
        if published:
            try:
                published_date = datetime.strptime(str(published), '%a, %d %b %Y %H:%M:%S %z')
            except:
                try:
                    published_date = datetime.strptime(str(published), '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    published_date = None
        else:
            published_date = None

        # Extract author
        author = entry.get('author', 'Unknown')
        if isinstance(author, dict):
            author = author.get('name', 'Unknown')

        # Extract domain from link
        domain = ''
        if link:
            parsed_url = urlparse(str(link))
            domain = parsed_url.netloc

        return {
            'title': title,
            'content': content_text,
            'url': link,
            'domain': domain,
            'author': author,
            'published_date': published_date.isoformat() if published_date else None,
            'source': 'rss',
            'raw_entry': entry
        }

    def fetch_multiple_feeds(self, feed_urls: List[str], max_items_per_feed: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch content from multiple RSS feeds.

        Args:
            feed_urls: List of RSS feed URLs
            max_items_per_feed: Maximum items to fetch from each feed

        Returns:
            Combined list of content from all feeds
        """
        all_content = []

        for feed_url in feed_urls:
            try:
                print(f"📡 Fetching content from: {feed_url}")
                feed_content = self.fetch_rss_feed(feed_url, max_items_per_feed)
                all_content.extend(feed_content)
                print(f"✅ Retrieved {len(feed_content)} items from {feed_url}")
            except Exception as e:
                print(f"⚠️  Could not fetch {feed_url}: {str(e)}")

        return all_content

    def fetch_feed_with_fallback(self, primary_url: str, fallback_urls: Optional[List[str]] = None, max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch from primary URL with fallback options.

        Args:
            primary_url: Primary RSS feed URL
            fallback_urls: List of fallback URLs to try if primary fails
            max_items: Maximum items to fetch

        Returns:
            List of content items
        """
        urls_to_try = [primary_url]
        if fallback_urls:
            urls_to_try.extend(fallback_urls)

        for url in urls_to_try:
            try:
                return self.fetch_rss_feed(url, max_items)
            except Exception as e:
                print(f"⚠️  Could not fetch {url}: {str(e)}")
                continue

        return []  # All URLs failed

    def get_content_for_publishing(self, content_item: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Prepare content for publishing to a specific platform.

        Args:
            content_item: Content item (RSS or VisualPing)
            platform: Target platform

        Returns:
            Dictionary with platform-specific content
        """
        base_content = content_item['content']

        # Clean up content
        clean_content = self._clean_content_for_publishing(base_content)

        if platform.lower() == 'facebook':
            # Facebook format
            return {
                'title': content_item['title'],
                'content': clean_content,
                'source_url': content_item['url'],
                'source_name': content_item['domain'],
                'image_url': self._extract_image_url(content_item)
            }
        elif platform.lower() == 'instagram':
            # Instagram format (requires image)
            caption = f"{content_item['title']}\n\n{clean_content[:2000]}"  # Instagram caption limit
            return {
                'title': content_item['title'],
                'content': caption,
                'source_url': content_item['url'],
                'source_name': content_item['domain'],
                'image_url': self._extract_image_url(content_item) or 'https://via.placeholder.com/1080x1080'  # Fallback
            }
        else:
            return {
                'title': content_item['title'],
                'content': clean_content,
                'source_url': content_item['url'],
                'source_name': content_item['domain'],
                'image_url': self._extract_image_url(content_item)
            }

    def _clean_content_for_publishing(self, content: str) -> str:
        """
        Clean content for publishing to social media platforms.

        Args:
            content: Raw content text

        Returns:
            Cleaned content suitable for publishing
        """
        # Remove excessive whitespace
        content = ' '.join(content.split())

        # Limit length for social media
        if len(content) > 3000:  # Reasonable limit for most platforms
            content = content[:2997] + '...'

        return content

    def _extract_image_url(self, content_item: Dict[str, Any]) -> Optional[str]:
        """
        Extract image URL from content item.

        Args:
            content_item: Content item

        Returns:
            Image URL if found, None otherwise
        """
        # For VisualPing content, return None (no direct image extraction)
        if content_item.get('source') == 'visualping':
            return None

        # For RSS content, check various possible locations for images
        raw_entry = content_item.get('raw_entry', {})

        # Try media_content
        if 'media_content' in raw_entry:
            for media in raw_entry.media_content:
                if media.get('medium') == 'image':
                    return media.get('url')

        # Try media_thumbnail
        if 'media_thumbnail' in raw_entry:
            for media in raw_entry.media_thumbnail:
                if media.get('url'):
                    return media.get('url')

        # Try enclosure
        if 'enclosures' in raw_entry:
            for enclosure in raw_entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href')

        # Try to find img tags in content
        content = content_item.get('content', '')
        if '<img' in content:
            # Simple extraction - could be improved with proper HTML parsing
            start = content.find('src="') + 5
            if start > 5:
                end = content.find('"', start)
                if end > start:
                    return content[start:end]

        return None

    def _has_media_content(self, content_item: Dict[str, Any]) -> bool:
        """
        Check if a content item contains media (images or videos).

        Args:
            content_item: Content item

        Returns:
            True if item has media content, False otherwise
        """
        # For VisualPing content, check has_media flag
        if content_item.get('source') == 'visualping':
            return content_item.get('has_media', False)

        # For RSS content, check various possible locations for media
        raw_entry = content_item.get('raw_entry', {})

        # Try media_content
        if 'media_content' in raw_entry:
            for media in raw_entry.media_content:
                if media.get('medium') in ['image', 'video']:
                    return True

        # Try media_thumbnail
        if 'media_thumbnail' in raw_entry:
            for media in raw_entry.media_thumbnail:
                if media.get('url'):
                    return True

        # Try enclosure
        if 'enclosures' in raw_entry:
            for enclosure in raw_entry.enclosures:
                if enclosure.get('type', '').startswith(('image/', 'video/')):
                    return True

        # Try to find img/video tags in content
        content = content_item.get('content', '')
        if '<img' in content or '<video' in content:
            return True

        return False

    def validate_rss_url(self, rss_url: str) -> bool:
        """
        Validate if a URL is likely an RSS feed.

        Args:
            rss_url: URL to validate

        Returns:
            True if URL appears to be valid RSS feed, False otherwise
        """
        try:
            # Check URL format
            parsed = urlparse(rss_url)
            if not all([parsed.scheme, parsed.netloc]):
                return False

            # Try to fetch and parse the feed
            feed = feedparser.parse(rss_url)
            return not feed.bozo and len(feed.entries) > 0

        except Exception as e:
            print(f"⚠️  RSS URL validation failed: {str(e)}")
            return False

    def fetch_visualping_content(self, url_id: str, require_media: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch content from VisualPing API for a specific URL.

        Args:
            url_id: VisualPing URL ID to fetch content for
            require_media: If True, only return content with visual changes (default: True)

        Returns:
            Dictionary with VisualPing content and metadata, or None if no media content found
        """
        try:
            # Check if we have an API key
            if not self.visualping_api_key:
                return self._mock_visualping_response(url_id)

            # Make API request to VisualPing
            endpoint = f"{self.visualping_base_url}/checks/{url_id}"
            response = requests.get(endpoint, headers=self.visualping_headers)

            if response.status_code == 200:
                api_data = response.json()
                return self._process_visualping_response(api_data, url_id, require_media)
            else:
                print(f"⚠️  VisualPing API error: {response.status_code} - {response.text}")
                return self._mock_visualping_response(url_id)

        except Exception as e:
            print(f"⚠️  Could not fetch VisualPing content: {str(e)}")
            return self._mock_visualping_response(url_id)

    def _process_visualping_response(self, api_data: Dict[str, Any], url_id: str, require_media: bool = True) -> Optional[Dict[str, Any]]:
        """
        Process raw VisualPing API response into standardized format.

        Args:
            api_data: Raw API response from VisualPing
            url_id: VisualPing URL ID
            require_media: If True, only process changes with visual content

        Returns:
            Processed content dictionary or None if no media content
        """
        # Extract relevant information from API response
        check_data = api_data.get('check', {})
        state = check_data.get('state', 'unknown')
        url = check_data.get('url', f'https://visualping.io/check/{url_id}')

        # Extract domain from URL
        domain = self._extract_domain(url)

        # Check if this change has visual media content
        has_media = self._has_visual_media(check_data)

        if require_media and not has_media:
            return None

        # Determine change type and content
        if state == 'changed':
            change_type = 'visual_change' if has_media else 'content_change'
            content = f"Visual content change detected on {url}\n\n" if has_media else f"Content change detected on {url}\n\n"
            content += f"Change type: {check_data.get('change_type', 'unknown')}\n"
            content += f"Change percentage: {check_data.get('change_percentage', 0)}%\n"
            content += f"Detected at: {check_data.get('detected_at', datetime.now().isoformat())}"

            # Add media-specific information if available
            if has_media:
                content += f"\n\n📸 Visual changes detected in this update"
        else:
            change_type = 'no_change'
            content = f"No significant visual changes detected on {url}"

        return {
            'title': f"VisualPing Alert: {state.capitalize()} - {domain}",
            'content': content,
            'url': url,
            'domain': domain,
            'source': 'visualping',
            'change_type': change_type,
            'state': state,
            'has_media': has_media,
            'detected_at': check_data.get('detected_at', datetime.now().isoformat()),
            'raw_data': api_data
        }

    def _mock_visualping_response(self, url_id: str) -> Dict[str, Any]:
        """
        Generate a mock VisualPing response for testing.

        Args:
            url_id: VisualPing URL ID

        Returns:
            Mock content dictionary
        """
        mock_url = f"https://example.com/{url_id}"
        domain = self._extract_domain(mock_url)

        return {
            'title': f"VisualPing Alert for {url_id}",
            'content': f"Content change detected on monitored URL {mock_url}\n\n"
                      f"This is a mock response. In production, this would contain "
                      f"actual VisualPing API data including change details, "
                      f"screenshots, and timestamps.",
            'url': mock_url,
            'domain': domain,
            'source': 'visualping',
            'change_type': 'content_change',
            'state': 'changed',
            'detected_at': datetime.now().isoformat(),
            'raw_data': {'mock': True, 'url_id': url_id}
        }

    def _has_visual_media(self, check_data: Dict[str, Any]) -> bool:
        """
        Check if VisualPing check data contains visual media changes.

        Args:
            check_data: VisualPing check data

        Returns:
            True if visual media changes detected, False otherwise
        """
        # Check for visual change indicators
        change_type = check_data.get('change_type', '').lower()
        change_percentage = check_data.get('change_percentage', 0)

        # Consider it visual media if:
        # 1. Change type suggests visual content
        # 2. Significant change percentage (greater than 5%)
        # 3. Has screenshot data
        visual_indicators = ['visual', 'image', 'layout', 'design']
        has_visual_change = any(indicator in change_type for indicator in visual_indicators)

        significant_change = change_percentage > 5
        has_screenshot = 'screenshot' in check_data or 'before_screenshot' in check_data

        return has_visual_change or significant_change or has_screenshot

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Extracted domain
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown.domain"

    def set_visualping_api_key(self, api_key: str):
        """
        Set or update the VisualPing API key.

        Args:
            api_key: VisualPing API key
        """
        self.visualping_api_key = api_key
        self.visualping_headers['Authorization'] = f'Bearer {api_key}'

def main():
    """Test the content fetcher functionality."""
    print("📡 Content Fetcher Test (RSS + VisualPing)")
    print("=" * 50)

    try:
        fetcher = ContentFetcher()
        print("✅ Content fetcher initialized")

        # Test RSS functionality
        print("\n🌍 Testing RSS functionality...")
        sample_feeds = [
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://www.theguardian.com/world/rss'
        ]

        for feed_url in sample_feeds[:1]:  # Test with just one to avoid rate limiting
            try:
                print(f"\n📰 Fetching: {feed_url}")
                feed_items = fetcher.fetch_rss_feed(feed_url, max_items=2)

                if feed_items:
                    print(f"✅ Retrieved {len(feed_items)} items")

                    # Show first item details
                    first_item = feed_items[0]
                    print(f"\n📄 First Item:")
                    print(f"   Title: {first_item['title']}")
                    print(f"   Source: {first_item['domain']}")
                    print(f"   Published: {first_item['published_date']}")
                    print(f"   Content preview: {first_item['content'][:200]}...")

                    # Test platform preparation
                    print(f"\n📱 Preparing for Facebook:")
                    fb_content = fetcher.get_content_for_publishing(first_item, 'facebook')
                    print(f"   Facebook content: {fb_content['content'][:100]}...")

                    print(f"\n📸 Preparing for Instagram:")
                    insta_content = fetcher.get_content_for_publishing(first_item, 'instagram')
                    print(f"   Instagram caption: {insta_content['content'][:100]}...")
                    print(f"   Has image URL: {'✅ Yes' if insta_content['image_url'] else '❌ No'}")

                else:
                    print("❌ No items retrieved")

            except Exception as e:
                print(f"⚠️  Could not fetch {feed_url}: {str(e)}")

        # Test VisualPing functionality (mock)
        print("\n🔍 Testing VisualPing functionality...")
        try:
            vp_content = fetcher.fetch_visualping_content("test_url_123")
            if vp_content:
                print(f"✅ VisualPing content fetched: {vp_content['title']}")
                print(f"   Domain: {vp_content['domain']}")
                print(f"   State: {vp_content['state']}")
                print(f"   Content: {vp_content['content'][:150]}...")
            else:
                print("ℹ️  No visual content found (media filtering enabled)")
        except Exception as e:
            print(f"⚠️  VisualPing test failed: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()