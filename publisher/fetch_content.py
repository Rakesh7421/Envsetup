#!/usr/bin/env python3
"""
RSS Content Fetcher Module
Fetches content from RSS feeds and prepares it for publishing.
"""

import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import html2text
import requests
from urllib.parse import urlparse

class RSSContentFetcher:
    """
    Fetches and processes content from RSS feeds.
    """

    def __init__(self):
        """
        Initialize the RSS content fetcher.
        """
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False

    def fetch_rss_feed(self, rss_url: str, max_items: int = 5, require_media: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            require_media: If True, only return items that have images/videos

        Returns:
            List of parsed feed items
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

    def get_content_for_publishing(self, rss_item: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Prepare RSS content for publishing to a specific platform.

        Args:
            rss_item: RSS content item
            platform: Target platform

        Returns:
            Dictionary with platform-specific content
        """
        base_content = rss_item['content']

        # Clean up content
        clean_content = self._clean_content_for_publishing(base_content)

        if platform.lower() == 'facebook':
            # Facebook format
            return {
                'title': rss_item['title'],
                'content': clean_content,
                'source_url': rss_item['url'],
                'source_name': rss_item['domain'],
                'image_url': self._extract_image_url(rss_item)
            }
        elif platform.lower() == 'instagram':
            # Instagram format (requires image)
            caption = f"{rss_item['title']}\n\n{clean_content[:2000]}"  # Instagram caption limit
            return {
                'title': rss_item['title'],
                'content': caption,
                'source_url': rss_item['url'],
                'source_name': rss_item['domain'],
                'image_url': self._extract_image_url(rss_item) or 'https://via.placeholder.com/1080x1080'  # Fallback
            }
        else:
            return {
                'title': rss_item['title'],
                'content': clean_content,
                'source_url': rss_item['url'],
                'source_name': rss_item['domain'],
                'image_url': self._extract_image_url(rss_item)
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

    def _extract_image_url(self, rss_item: Dict[str, Any]) -> Optional[str]:
        """
        Extract image URL from RSS item.

        Args:
            rss_item: RSS content item

        Returns:
            Image URL if found, None otherwise
        """
        # Check various possible locations for images
        raw_entry = rss_item.get('raw_entry', {})

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
        content = rss_item.get('content', '')
        if '<img' in content:
            # Simple extraction - could be improved with proper HTML parsing
            start = content.find('src="') + 5
            if start > 5:
                end = content.find('"', start)
                if end > start:
                    return content[start:end]

        return None

    def _has_media_content(self, rss_item: Dict[str, Any]) -> bool:
        """
        Check if an RSS item contains media (images or videos).

        Args:
            rss_item: RSS content item

        Returns:
            True if item has media content, False otherwise
        """
        # Check various possible locations for media
        raw_entry = rss_item.get('raw_entry', {})

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
        content = rss_item.get('content', '')
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

def main():
    """Test the RSS content fetcher functionality."""
    print("📡 RSS Content Fetcher Test")
    print("=" * 40)

    try:
        fetcher = RSSContentFetcher()
        print("✅ RSS content fetcher initialized")

        # Test with sample RSS feeds
        sample_feeds = [
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://www.theguardian.com/world/rss'
        ]

        print("\n🌍 Testing with sample RSS feeds...")
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

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()