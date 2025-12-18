#!/usr/bin/env python3
"""
RSS Content Fetcher Module
Fetches and processes content from RSS feeds.
"""

import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import html2text
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
            'https://feeds.bbci.co.uk/news/rss.xml'
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

                else:
                    print("❌ No items retrieved")

            except Exception as e:
                print(f"⚠️  Could not fetch {feed_url}: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()