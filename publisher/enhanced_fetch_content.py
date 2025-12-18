#!/usr/bin/env python3
"""
Enhanced Content Fetcher Module
Integrates comprehensive media validation with existing RSS and VisualPing functionality.
"""

import logging
import sys
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import importlib.util
import os
import feedparser
from urllib.parse import urlparse
import requests
import html2text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedContentFetcher:
    """
    Enhanced content fetcher with comprehensive media validation capabilities.
    Extends the existing RSS and VisualPing functionality with validation.
    """

    def __init__(self, visualping_api_key: Optional[str] = None):
        """
        Initialize the enhanced content fetcher.

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

        # Initialize validation components
        self.feed_parser = None
        self.media_validator = None
        self._initialize_validation_components()

    def _initialize_validation_components(self):
        """
        Initialize media validation and feed parsing components.
        """
        try:
            from publisher.feed_parser import FeedParser
            from publisher.media_validator import MediaValidator
            self.feed_parser = FeedParser()
            self.media_validator = MediaValidator()
            logger.info("✅ Media validation components initialized")
        except Exception as e:
            logger.warning(f"Could not initialize validation components: {str(e)}")
            # Fallback to basic functionality
            self.feed_parser = None
            self.media_validator = None

    def fetch_and_validate_feed_directory(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Fetch and validate all feeds in the specified directory with comprehensive validation.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with comprehensive validation results
        """
        if not self.feed_parser:
            return {
                'error': 'Validation components not available',
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR'
            }

        try:
            # Parse and validate the feed directory
            parsing_results = self.feed_parser.parse_feed_directory(feed_directory)

            # Generate structured output
            structured_output = self.feed_parser.generate_structured_output(parsing_results)

            # Add additional validation metadata
            enhanced_results = {
                **structured_output,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_system': 'enhanced',
                'minimum_media_requirement_met': structured_output['validation_summary']['has_minimum_media'],
                'recommendations': self._generate_recommendations(structured_output)
            }

            return enhanced_results

        except Exception as e:
            logger.error(f"Error in feed directory validation: {str(e)}")
            return {
                'error': f"Validation failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR'
            }

    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on validation results.

        Args:
            validation_results: Validation results dictionary

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check overall status
        status = validation_results['validation_summary']['status']
        if status == 'SUCCESS':
            recommendations.append("✅ All feeds are properly configured with media support")
        elif status == 'PARTIAL_SUCCESS':
            recommendations.append("⚠️ Some feeds have issues but media requirements are met")
        elif status == 'VALIDATION_FAILURE':
            recommendations.append("❌ Media requirements not met - add feeds with image/video content")
        elif status == 'LOADING_ERROR':
            recommendations.append("❌ Feed loading errors - check feed module structure")

        # Check media inventory
        media_inventory = validation_results['media_inventory']
        if media_inventory['images'] == 0 and media_inventory['videos'] == 0:
            recommendations.append("📸 No image or video capabilities detected - add media-rich feeds")
        elif media_inventory['images'] == 0:
            recommendations.append("📸 No image capabilities detected - consider adding feeds with images")
        elif media_inventory['videos'] == 0:
            recommendations.append("🎥 No video capabilities detected - consider adding feeds with videos")

        # Check for errors
        if validation_results['errors']:
            recommendations.append(f"🔧 Fix {len(validation_results['errors'])} errors for optimal performance")

        return recommendations

    def fetch_rss_feed_with_validation(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> Dict[str, Any]:
        """
        Fetch RSS feed with comprehensive media validation.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            require_media: If True, only return items with media

        Returns:
            Dictionary with validation results and content
        """
        if not self.feed_parser:
            # Fallback to basic RSS fetching
            return self._fallback_rss_fetch(rss_url, max_items, require_media)

        try:
            # Parse the feed with validation
            parsing_results = self.feed_parser.parse_rss_feed(rss_url, max_items, require_media)

            # Enhance with additional validation
            enhanced_results = {
                **parsing_results,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_system': 'enhanced',
                'media_requirement_met': parsing_results['items_with_media'] > 0 if require_media else True,
                'feed_quality_score': self._calculate_feed_quality_score(parsing_results)
            }

            return enhanced_results

        except Exception as e:
            logger.error(f"Error in validated RSS fetch: {str(e)}")
            return {
                'error': f"Validation failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR',
                'fallback_results': self._fallback_rss_fetch(rss_url, max_items, require_media)
            }

    def _calculate_feed_quality_score(self, parsing_results: Dict[str, Any]) -> float:
        """
        Calculate a quality score for the feed based on validation results.

        Args:
            parsing_results: Feed parsing results

        Returns:
            Quality score between 0 and 1
        """
        try:
            total_items = parsing_results['items_parsed']
            items_with_media = parsing_results['items_with_media']
            errors = len(parsing_results['errors'])
            warnings = len(parsing_results['warnings'])

            if total_items == 0:
                return 0.0

            # Calculate score components
            media_score = items_with_media / total_items
            error_penalty = max(0, 1 - (errors * 0.1))  # 10% penalty per error
            warning_penalty = max(0, 1 - (warnings * 0.05))  # 5% penalty per warning

            # Combine scores
            quality_score = (media_score * 0.5) + (error_penalty * 0.3) + (warning_penalty * 0.2)

            return round(max(0, min(1, quality_score)), 2)

        except Exception as e:
            logger.warning(f"Could not calculate quality score: {str(e)}")
            return 0.0

    def _fallback_rss_fetch(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> Dict[str, Any]:
        """
        Fallback RSS fetching method when validation components are unavailable.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            require_media: If True, only return items with media

        Returns:
            Dictionary with basic RSS fetch results
        """
        fallback_results = {
            'timestamp': datetime.now().isoformat(),
            'feed_url': rss_url,
            'status': 'FALLBACK',
            'items': [],
            'errors': [],
            'warnings': ['Using fallback RSS fetching - validation components unavailable']
        }

        try:
            # Basic RSS parsing
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                fallback_results['errors'].append(f"Feed parsing error: {feed.bozo_exception}")
                fallback_results['status'] = 'ERROR'
                return fallback_results

            # Process items
            items = []
            for entry in feed.entries[:max_items]:
                try:
                    item = self._process_feed_entry_fallback(entry)

                    # Filter for media if required
                    if require_media:
                        if self._has_media_content_fallback(item):
                            items.append(item)
                    else:
                        items.append(item)

                except Exception as e:
                    fallback_results['errors'].append(f"Error processing item: {str(e)}")

            fallback_results['items'] = items
            fallback_results['status'] = 'SUCCESS' if items else 'NO_CONTENT'

        except Exception as e:
            fallback_results['errors'].append(f"Fallback fetch failed: {str(e)}")
            fallback_results['status'] = 'ERROR'

        return fallback_results

    def _process_feed_entry_fallback(self, entry: feedparser.FeedParserDict) -> Dict[str, Any]:
        """
        Process a feed entry in fallback mode.

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

    def _has_media_content_fallback(self, content_item: Dict[str, Any]) -> bool:
        """
        Check if a content item contains media in fallback mode.

        Args:
            content_item: Content item

        Returns:
            True if item has media content, False otherwise
        """
        # Check various possible locations for media
        raw_entry = content_item.get('raw_entry', {})

        # Try media_content
        if hasattr(raw_entry, 'media_content'):
            for media in raw_entry.media_content:
                if hasattr(media, 'medium') and media.get('medium') in ['image', 'video']:
                    return True

        # Try media_thumbnail
        if hasattr(raw_entry, 'media_thumbnail'):
            for media in raw_entry.media_thumbnail:
                if media.get('url'):
                    return True

        # Try enclosure
        if hasattr(raw_entry, 'enclosures'):
            for enclosure in raw_entry.enclosures:
                enclosure_type = str(enclosure.get('type', '')).lower()
                if enclosure_type.startswith(('image/', 'video/')):
                    return True

        # Try to find img/video tags in content
        content = content_item.get('content', '')
        if '<img' in content or '<video' in content:
            return True

        return False

    def validate_media_url(self, media_url: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Validate that a media URL is accessible and returns valid content.

        Args:
            media_url: URL to validate
            timeout: Request timeout in seconds

        Returns:
            Dictionary with validation results
        """
        if self.media_validator:
            return self.media_validator.validate_media_url(media_url, timeout)
        else:
            # Fallback validation
            return self._fallback_media_url_validation(media_url, timeout)

    def _fallback_media_url_validation(self, media_url: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Fallback media URL validation.

        Args:
            media_url: URL to validate
            timeout: Request timeout in seconds

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'url': media_url,
            'is_valid': False,
            'is_accessible': False,
            'content_type': None,
            'content_length': 0,
            'status_code': None,
            'error': None,
            'warnings': []
        }

        try:
            # Basic URL validation
            parsed_url = urlparse(media_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                validation_result['error'] = "Invalid URL format"
                return validation_result

            # Make HEAD request to check URL accessibility
            try:
                response = requests.head(media_url, timeout=timeout, allow_redirects=True)
                validation_result['status_code'] = response.status_code

                if response.status_code == 200:
                    validation_result['is_accessible'] = True
                    validation_result['content_type'] = response.headers.get('Content-Type', '')
                    validation_result['content_length'] = int(response.headers.get('Content-Length', 0))

                    # Validate content type
                    if validation_result['content_type'].startswith(('image/', 'video/')):
                        validation_result['is_valid'] = True
                    else:
                        validation_result['warnings'].append(f"Unexpected content type: {validation_result['content_type']}")

                else:
                    validation_result['error'] = f"HTTP {response.status_code}"

            except requests.RequestException as e:
                validation_result['error'] = f"Request failed: {str(e)}"

        except Exception as e:
            validation_result['error'] = f"Validation error: {str(e)}"

        return validation_result

    async def fetch_and_validate_feed_directory_async(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Asynchronously fetch and validate all feeds in the specified directory.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with comprehensive validation results
        """
        if not self.feed_parser:
            return {
                'error': 'Validation components not available',
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR'
            }

        try:
            # Parse and validate the feed directory asynchronously
            parsing_results = await self.feed_parser.parse_feed_directory_async(feed_directory)

            # Generate structured output
            structured_output = self.feed_parser.generate_structured_output(parsing_results)

            # Add additional validation metadata
            enhanced_results = {
                **structured_output,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_system': 'enhanced_async',
                'minimum_media_requirement_met': structured_output['validation_summary']['has_minimum_media'],
                'recommendations': self._generate_recommendations(structured_output)
            }

            return enhanced_results

        except Exception as e:
            logger.error(f"Error in async feed directory validation: {str(e)}")
            return {
                'error': f"Async validation failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR'
            }

    async def fetch_rss_feed_with_validation_async(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> Dict[str, Any]:
        """
        Asynchronously fetch RSS feed with comprehensive media validation.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to fetch
            require_media: If True, only return items with media

        Returns:
            Dictionary with validation results and content
        """
        if not self.feed_parser:
            # Fallback to basic RSS fetching
            return self._fallback_rss_fetch(rss_url, max_items, require_media)

        try:
            # Parse the feed with validation asynchronously
            parsing_results = await self.feed_parser.parse_rss_feed_async(rss_url, max_items, require_media)

            # Enhance with additional validation
            enhanced_results = {
                **parsing_results,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_system': 'enhanced_async',
                'media_requirement_met': parsing_results['items_with_media'] > 0 if require_media else True,
                'feed_quality_score': self._calculate_feed_quality_score(parsing_results)
            }

            return enhanced_results

        except Exception as e:
            logger.error(f"Error in async validated RSS fetch: {str(e)}")
            return {
                'error': f"Async validation failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'ERROR',
                'fallback_results': self._fallback_rss_fetch(rss_url, max_items, require_media)
            }

    def get_content_for_publishing(self, content_item: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Prepare content for publishing to a specific platform (backward compatible method).

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
        if hasattr(raw_entry, 'media_content'):
            for media in raw_entry.media_content:
                if hasattr(media, 'medium') and media.get('medium') == 'image':
                    return media.get('url')

        # Try media_thumbnail
        if hasattr(raw_entry, 'media_thumbnail'):
            for media in raw_entry.media_thumbnail:
                if media.get('url'):
                    return media.get('url')

        # Try enclosure
        if hasattr(raw_entry, 'enclosures'):
            for enclosure in raw_entry.enclosures:
                if str(enclosure.get('type', '')).startswith('image/'):
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

    def fetch_visualping_content(self, url_id: str, require_media: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch content from VisualPing API for a specific URL (backward compatible method).

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
    """Test the enhanced content fetcher functionality."""
    print("🔍 Enhanced Content Fetcher Test")
    print("=" * 50)

    try:
        fetcher = EnhancedContentFetcher()
        print("✅ Enhanced content fetcher initialized")

        # Test feed directory validation
        print("\n📁 Testing feed directory validation...")
        validation_results = fetcher.fetch_and_validate_feed_directory()

        print(f"✅ Validation completed with status: {validation_results.get('validation_summary', {}).get('status', 'UNKNOWN')}")
        print(f"   Has minimum media: {'✅ Yes' if validation_results.get('minimum_media_requirement_met') else '❌ No'}")
        print(f"   Total media count: {validation_results.get('validation_summary', {}).get('total_media_count', 0)}")

        # Show recommendations
        if validation_results.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for recommendation in validation_results['recommendations']:
                print(f"   {recommendation}")

        # Test RSS feed validation
        print(f"\n🌐 Testing RSS feed validation...")
        test_feed_url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        try:
            rss_results = fetcher.fetch_rss_feed_with_validation(test_feed_url, max_items=2)
            print(f"   RSS Feed Status: {rss_results.get('status')}")
            print(f"   Items Parsed: {rss_results.get('items_parsed')}")
            print(f"   Items with Media: {rss_results.get('items_with_media')}")
            print(f"   Feed Quality Score: {rss_results.get('feed_quality_score', 0)}")

            if rss_results.get('content_items'):
                first_item = rss_results['content_items'][0]
                print(f"   First Item: {first_item.get('title')}")
                print(f"   Has Media: {'✅ Yes' if first_item.get('has_media') else '❌ No'}")

        except Exception as e:
            print(f"   RSS validation test failed: {str(e)}")

        # Test media URL validation
        print(f"\n🔗 Testing media URL validation...")
        test_url = "https://via.placeholder.com/350x150"
        url_validation = fetcher.validate_media_url(test_url)
        print(f"   Test URL: {test_url}")
        print(f"   Is Valid: {'✅ Yes' if url_validation['is_valid'] else '❌ No'}")
        print(f"   Status: {url_validation.get('status_code')}")
        print(f"   Content Type: {url_validation.get('content_type')}")

        # Test backward compatibility
        print(f"\n🔄 Testing backward compatibility...")
        # Test with mock content item
        mock_item = {
            'title': 'Test Content',
            'content': 'This is test content with some details.',
            'url': 'https://example.com/test',
            'domain': 'example.com',
            'raw_entry': {}
        }

        fb_content = fetcher.get_content_for_publishing(mock_item, 'facebook')
        print(f"   Facebook content prepared: {'✅ Yes' if fb_content else '❌ No'}")
        print(f"   Content length: {len(fb_content.get('content', ''))} characters")

    except Exception as e:
        print(f"❌ Enhanced fetcher test failed: {str(e)}")

if __name__ == "__main__":
    main()