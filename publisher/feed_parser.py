#!/usr/bin/env python3
"""
Feed Parser Module
Parses and validates content feeds with comprehensive media validation.
"""

import logging
import sys
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import importlib.util
import os
import feedparser
from urllib.parse import urlparse
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FeedParser:
    """
    Parses and validates content feeds with comprehensive media validation.
    """

    def __init__(self):
        """
        Initialize the feed parser.
        """
        self.media_validator = None
        self.feed_modules = {}
        self.supported_feed_types = ['rss', 'atom', 'visualping']

    def load_feed_modules(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Load feed modules from the specified directory.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with loading results
        """
        loading_results = {
            'timestamp': datetime.now().isoformat(),
            'feed_directory': feed_directory,
            'modules_loaded': 0,
            'modules_failed': 0,
            'loaded_modules': [],
            'errors': []
        }

        try:
            # Clear existing modules
            self.feed_modules = {}

            # Get all Python files in the directory
            feed_files = []
            for filename in os.listdir(feed_directory):
                if filename.endswith('.py') and not filename.startswith('__'):
                    feed_files.append(filename)

            logger.info(f"Found {len(feed_files)} feed modules to load")

            # Load each feed module
            for feed_file in feed_files:
                module_name = feed_file.replace('.py', '')
                module_path = os.path.join(feed_directory, feed_file)

                try:
                    # Import the module dynamically
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        feed_module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = feed_module
                        spec.loader.exec_module(feed_module)

                        # Store the module
                        self.feed_modules[module_name] = feed_module
                        loading_results['loaded_modules'].append(module_name)
                        loading_results['modules_loaded'] += 1

                        logger.info(f"✅ Loaded feed module: {module_name}")

                    else:
                        error_msg = f"Could not load module spec: {feed_file}"
                        loading_results['errors'].append(error_msg)
                        loading_results['modules_failed'] += 1
                        logger.error(error_msg)

                except Exception as e:
                    error_msg = f"Error loading {feed_file}: {str(e)}"
                    loading_results['errors'].append(error_msg)
                    loading_results['modules_failed'] += 1
                    logger.error(error_msg)

        except Exception as e:
            loading_results['errors'].append(f"Module loading failed: {str(e)}")
            logger.error(f"Error loading feed modules: {str(e)}")

        return loading_results

    def parse_feed_directory(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Parse and validate all feeds in the specified directory.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with parsing and validation results
        """
        # First load the feed modules
        loading_results = self.load_feed_modules(feed_directory)

        # Then validate them using media validator
        if not self.media_validator:
            try:
                from media_validator import MediaValidator
                self.media_validator = MediaValidator()
            except ImportError:
                # Try alternative import path
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from media_validator import MediaValidator
                    self.media_validator = MediaValidator()
                except ImportError as e:
                    logger.error(f"Could not import MediaValidator: {str(e)}")
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'module_loading': loading_results,
                        'feed_validation': {'validation_status': 'ERROR', 'errors': [f'MediaValidator import failed: {str(e)}']},
                        'overall_status': 'ERROR'
                    }

        validation_results = self.media_validator.validate_feed_directory(feed_directory)

        # Combine results
        combined_results = {
            'timestamp': datetime.now().isoformat(),
            'module_loading': loading_results,
            'feed_validation': validation_results,
            'overall_status': self._determine_overall_status(loading_results, validation_results)
        }

        return combined_results

    def _determine_overall_status(self, loading_results: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """
        Determine overall parsing status based on loading and validation results.

        Args:
            loading_results: Module loading results
            validation_results: Feed validation results

        Returns:
            Overall status string
        """
        has_loading_errors = len(loading_results.get('errors', [])) > 0
        has_validation_errors = validation_results.get('total_errors', 0) > 0
        has_media = validation_results.get('total_media_count', 0) > 0
        modules_loaded = loading_results.get('modules_loaded', 0) > 0

        if has_loading_errors:
            return 'LOADING_ERROR'
        elif not modules_loaded:
            return 'NO_MODULES'
        elif has_validation_errors and not has_media:
            return 'VALIDATION_FAILURE'
        elif has_media and not has_validation_errors:
            return 'SUCCESS'
        elif has_media and has_validation_errors:
            return 'PARTIAL_SUCCESS'
        else:
            return 'UNKNOWN'

    def parse_rss_feed(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> Dict[str, Any]:
        """
        Parse an RSS feed with comprehensive validation.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to parse
            require_media: If True, only return items with media

        Returns:
            Dictionary with parsing results
        """
        parsing_result = {
            'timestamp': datetime.now().isoformat(),
            'feed_url': rss_url,
            'items_parsed': 0,
            'items_with_media': 0,
            'media_validation': [],
            'errors': [],
            'warnings': [],
            'feed_metadata': {},
            'content_items': []
        }

        try:
            # Validate URL format
            if not self._validate_url_format(rss_url):
                parsing_result['errors'].append("Invalid RSS URL format")
                return parsing_result

            # Parse the feed
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                parsing_result['errors'].append(f"Feed parsing error: {feed.bozo_exception}")
                return parsing_result

            # Extract feed metadata
            parsing_result['feed_metadata'] = self._extract_feed_metadata(feed)

            # Process feed items
            for entry in feed.entries[:max_items]:
                try:
                    item_result = self._process_feed_item(entry, require_media)
                    if item_result:
                        parsing_result['content_items'].append(item_result)

                        if item_result.get('has_media', False):
                            parsing_result['items_with_media'] += 1

                        # Add media validation results
                        if item_result.get('media_validation'):
                            parsing_result['media_validation'].extend(item_result['media_validation'])

                    parsing_result['items_parsed'] += 1

                except Exception as e:
                    parsing_result['errors'].append(f"Error processing item {entry.get('title', 'untitled')}: {str(e)}")
                    logger.error(f"Error processing feed item: {str(e)}")

            # Determine parsing status
            parsing_result['status'] = (
                'SUCCESS' if parsing_result['items_parsed'] > 0 and
                (not require_media or parsing_result['items_with_media'] > 0) else
                'PARTIAL' if parsing_result['items_parsed'] > 0 else
                'FAILURE'
            )

        except Exception as e:
            parsing_result['errors'].append(f"Feed parsing failed: {str(e)}")
            parsing_result['status'] = 'ERROR'
            logger.error(f"Error parsing RSS feed: {str(e)}")

        return parsing_result

    def _validate_url_format(self, url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL format is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False

    def _extract_feed_metadata(self, feed: feedparser.FeedParserDict) -> Dict[str, Any]:
        """
        Extract metadata from a parsed feed.

        Args:
            feed: Parsed feed object

        Returns:
            Dictionary with feed metadata
        """
        metadata = {
            'title': getattr(feed.feed, 'title', 'Untitled Feed'),
            'description': getattr(feed.feed, 'description', ''),
            'link': getattr(feed.feed, 'link', ''),
            'language': getattr(feed.feed, 'language', ''),
            'published': getattr(feed.feed, 'published', None),
            'updated': getattr(feed.feed, 'updated', None),
            'generator': getattr(feed.feed, 'generator', ''),
            'image': self._extract_feed_image(feed),
            'categories': []
        }

        # Convert dates to ISO format if they exist
        if metadata['published']:
            try:
                metadata['published'] = datetime.strptime(str(metadata['published']), '%a, %d %b %Y %H:%M:%S %z').isoformat()
            except:
                metadata['published'] = str(metadata['published'])

        if metadata['updated']:
            try:
                metadata['updated'] = datetime.strptime(str(metadata['updated']), '%a, %d %b %Y %H:%M:%S %z').isoformat()
            except:
                metadata['updated'] = str(metadata['updated'])

        # Extract categories (simplified to avoid type issues)
        try:
            if hasattr(feed.feed, 'tags'):
                tags = getattr(feed.feed, 'tags', [])
                if isinstance(tags, list):
                    for tag in tags:
                        if hasattr(tag, 'term'):
                            metadata['categories'].append(tag.term)
        except Exception as e:
            logger.warning(f"Could not extract categories: {str(e)}")

        return metadata

    def _extract_feed_image(self, feed: feedparser.FeedParserDict) -> Optional[Dict[str, Any]]:
        """
        Extract feed image information.

        Args:
            feed: Parsed feed object

        Returns:
            Dictionary with feed image information or None
        """
        try:
            if hasattr(feed.feed, 'image'):
                image = getattr(feed.feed, 'image', None)
                if image:
                    return {
                        'url': getattr(image, 'href', ''),
                        'title': getattr(image, 'title', ''),
                        'link': getattr(image, 'link', ''),
                        'width': getattr(image, 'width', None),
                        'height': getattr(image, 'height', None)
                    }
            return None
        except Exception as e:
            logger.warning(f"Could not extract feed image: {str(e)}")
            return None

    def _process_feed_item(self, entry: feedparser.FeedParserDict, require_media: bool) -> Optional[Dict[str, Any]]:
        """
        Process a single feed item with media validation.

        Args:
            entry: Feed entry
            require_media: If True, only process items with media

        Returns:
            Dictionary with processed item or None
        """
        try:
            item_result = {
                'title': entry.get('title', 'Untitled'),
                'link': entry.get('link', ''),
                'published': self._parse_entry_date(entry),
                'author': self._extract_author(entry),
                'content': self._extract_content(entry),
                'has_media': False,
                'media_validation': [],
                'warnings': []
            }

            # Check for media content
            media_info = self._extract_media_from_entry(entry)
            item_result['has_media'] = media_info['has_media']
            item_result['media_validation'] = media_info['validation_results']

            # If media is required and item has no media, return None
            if require_media and not item_result['has_media']:
                return None

            return item_result

        except Exception as e:
            logger.error(f"Error processing feed item: {str(e)}")
            return None

    def _parse_entry_date(self, entry: feedparser.FeedParserDict) -> Optional[str]:
        """
        Parse entry publication date.

        Args:
            entry: Feed entry

        Returns:
            ISO formatted date string or None
        """
        try:
            published = ''
            if hasattr(entry, 'published'):
                published = entry.published
            elif hasattr(entry, 'updated'):
                published = entry.updated

            if published:
                try:
                    published_date = datetime.strptime(str(published), '%a, %d %b %Y %H:%M:%S %z')
                    return published_date.isoformat()
                except:
                    try:
                        published_date = datetime.strptime(str(published), '%a, %d %b %Y %H:%M:%S %Z')
                        return published_date.isoformat()
                    except:
                        return str(published)

            return None
        except Exception as e:
            logger.warning(f"Could not parse entry date: {str(e)}")
            return None

    def _extract_author(self, entry: feedparser.FeedParserDict) -> str:
        """
        Extract author information from feed entry.

        Args:
            entry: Feed entry

        Returns:
            Author name string
        """
        try:
            author = entry.get('author', 'Unknown')
            if isinstance(author, dict):
                return author.get('name', 'Unknown')
            return str(author)
        except Exception as e:
            logger.warning(f"Could not extract author: {str(e)}")
            return 'Unknown'

    def _extract_content(self, entry: feedparser.FeedParserDict) -> str:
        """
        Extract content from feed entry.

        Args:
            entry: Feed entry

        Returns:
            Content string
        """
        try:
            content = ''
            if hasattr(entry, 'content') and entry.content:
                if isinstance(entry.content, list) and entry.content:
                    content = entry.content[0].get('value', '')
                else:
                    content = str(entry.content)
            elif hasattr(entry, 'summary'):
                content = str(entry.summary)

            return str(content) if content else ''
        except Exception as e:
            logger.warning(f"Could not extract content: {str(e)}")
            return ''

    def _extract_media_from_entry(self, entry: feedparser.FeedParserDict) -> Dict[str, Any]:
        """
        Extract media information from feed entry.

        Args:
            entry: Feed entry

        Returns:
            Dictionary with media information
        """
        media_info = {
            'has_media': False,
            'validation_results': []
        }

        try:
            # Check for media content
            if hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if hasattr(media, 'medium') and media.get('medium') in ['image', 'video']:
                        media_url = media.get('url')
                        if media_url:
                            validation = self._validate_media_url(str(media_url))
                            validation['media_type'] = media.get('medium')
                            media_info['validation_results'].append(validation)
                            media_info['has_media'] = True

            # Check for media thumbnail
            if hasattr(entry, 'media_thumbnail'):
                for media in entry.media_thumbnail:
                    media_url = media.get('url')
                    if media_url:
                        validation = self._validate_media_url(str(media_url))
                        validation['media_type'] = 'image'
                        media_info['validation_results'].append(validation)
                        media_info['has_media'] = True

            # Check for enclosures
            if hasattr(entry, 'enclosures'):
                for enclosure in entry.enclosures:
                    enclosure_type = str(enclosure.get('type', '')).lower()
                    if enclosure_type.startswith(('image/', 'video/')):
                        media_url = enclosure.get('href')
                        if media_url:
                            validation = self._validate_media_url(str(media_url))
                            validation['media_type'] = 'image' if enclosure_type.startswith('image/') else 'video'
                            media_info['validation_results'].append(validation)
                            media_info['has_media'] = True

        except Exception as e:
            logger.error(f"Error extracting media from entry: {str(e)}")

        return media_info

    def _validate_media_url(self, media_url: str) -> Dict[str, Any]:
        """
        Validate a media URL.

        Args:
            media_url: Media URL to validate

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'url': media_url,
            'is_valid': False,
            'is_accessible': False,
            'status_code': None,
            'error': None
        }

        try:
            # Basic URL validation
            parsed_url = urlparse(media_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                validation_result['error'] = "Invalid URL format"
                return validation_result

            # Make HEAD request to check URL accessibility
            try:
                response = requests.head(media_url, timeout=5, allow_redirects=True)
                validation_result['status_code'] = response.status_code

                if response.status_code == 200:
                    validation_result['is_accessible'] = True
                    content_type = response.headers.get('Content-Type', '').lower()

                    # Validate content type
                    if content_type.startswith(('image/', 'video/')):
                        validation_result['is_valid'] = True
                    else:
                        validation_result['error'] = f"Invalid content type: {content_type}"

                else:
                    validation_result['error'] = f"HTTP {response.status_code}"

            except requests.RequestException as e:
                validation_result['error'] = f"Request failed: {str(e)}"

        except Exception as e:
            validation_result['error'] = f"Validation error: {str(e)}"

        return validation_result

    async def parse_feed_directory_async(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Asynchronously parse and validate all feeds in the specified directory.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with parsing and validation results
        """
        # Load modules synchronously first
        loading_results = self.load_feed_modules(feed_directory)

        # Then validate asynchronously
        validation_results = await self._validate_feeds_async(feed_directory)

        # Combine results
        combined_results = {
            'timestamp': datetime.now().isoformat(),
            'module_loading': loading_results,
            'feed_validation': validation_results,
            'overall_status': self._determine_overall_status(loading_results, validation_results)
        }

        return combined_results

    async def _validate_feeds_async(self, feed_directory: str) -> Dict[str, Any]:
        """
        Asynchronously validate feed modules.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with validation results
        """
        if not self.media_validator:
            from publisher.media_validator import MediaValidator
            self.media_validator = MediaValidator()

        # For async validation, we'll use the synchronous method for now
        # In a real implementation, this would be properly async
        return self.media_validator.validate_feed_directory(feed_directory)

    async def parse_rss_feed_async(self, rss_url: str, max_items: int = 5, require_media: bool = True) -> Dict[str, Any]:
        """
        Asynchronously parse an RSS feed with comprehensive validation.

        Args:
            rss_url: URL of the RSS feed
            max_items: Maximum number of items to parse
            require_media: If True, only return items with media

        Returns:
            Dictionary with parsing results
        """
        # Use synchronous method for now
        # In a real implementation, this would use aiohttp for async requests
        return self.parse_rss_feed(rss_url, max_items, require_media)

    def generate_structured_output(self, parsing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured output from parsing results.

        Args:
            parsing_results: Parsing results dictionary

        Returns:
            Structured output dictionary
        """
        structured_output = {
            'validation_summary': {
                'timestamp': parsing_results.get('timestamp'),
                'status': parsing_results.get('overall_status', 'UNKNOWN'),
                'modules_loaded': parsing_results.get('module_loading', {}).get('modules_loaded', 0),
                'modules_failed': parsing_results.get('module_loading', {}).get('modules_failed', 0),
                'total_media_count': parsing_results.get('feed_validation', {}).get('total_media_count', 0),
                'total_errors': parsing_results.get('feed_validation', {}).get('total_errors', 0),
                'total_warnings': parsing_results.get('feed_validation', {}).get('total_warnings', 0),
                'has_minimum_media': parsing_results.get('feed_validation', {}).get('total_media_count', 0) > 0
            },
            'module_details': [],
            'feed_details': [],
            'media_inventory': {
                'images': 0,
                'videos': 0,
                'total': 0,
                'types': []
            },
            'warnings': [],
            'errors': []
        }

        try:
            # Add module loading details
            for module_name in parsing_results.get('module_loading', {}).get('loaded_modules', []):
                structured_output['module_details'].append({
                    'module_name': module_name,
                    'status': 'LOADED'
                })

            for error in parsing_results.get('module_loading', {}).get('errors', []):
                structured_output['errors'].append(f"Module loading error: {error}")

            # Add feed validation details
            for feed_result in parsing_results.get('feed_validation', {}).get('feeds_validated', []):
                structured_output['feed_details'].append({
                    'feed_name': feed_result.get('feed_name'),
                    'is_valid': feed_result.get('is_valid', False),
                    'has_media_support': feed_result.get('has_media_support', False),
                    'media_count': feed_result.get('media_count', 0),
                    'media_types': feed_result.get('media_types', []),
                    'warnings': feed_result.get('warnings', []),
                    'errors': feed_result.get('errors', [])
                })

                # Update media inventory
                for media_type in feed_result.get('media_types', []):
                    if media_type not in structured_output['media_inventory']['types']:
                        structured_output['media_inventory']['types'].append(media_type)

                # Count image/video types
                if 'image' in feed_result.get('media_types', []):
                    structured_output['media_inventory']['images'] += 1
                if 'video' in feed_result.get('media_types', []):
                    structured_output['media_inventory']['videos'] += 1

            # Update totals
            structured_output['media_inventory']['total'] = (
                structured_output['media_inventory']['images'] +
                structured_output['media_inventory']['videos']
            )

            # Collect all warnings and errors from feed validation
            for feed_result in parsing_results.get('feed_validation', {}).get('feeds_validated', []):
                structured_output['warnings'].extend(feed_result.get('warnings', []))
                structured_output['errors'].extend(feed_result.get('errors', []))

        except Exception as e:
            logger.error(f"Error generating structured output: {str(e)}")
            structured_output['errors'].append(f"Output generation error: {str(e)}")

        return structured_output

def main():
    """Test the feed parser functionality."""
    print("📡 Feed Parser Test")
    print("=" * 40)

    try:
        parser = FeedParser()

        # Test feed directory parsing
        print("\n📁 Testing feed directory parsing...")
        parsing_results = parser.parse_feed_directory()

        print(f"✅ Parsing completed with status: {parsing_results.get('overall_status')}")
        print(f"   Modules loaded: {parsing_results.get('module_loading', {}).get('modules_loaded', 0)}")
        print(f"   Modules failed: {parsing_results.get('module_loading', {}).get('modules_failed', 0)}")
        print(f"   Total media count: {parsing_results.get('feed_validation', {}).get('total_media_count', 0)}")
        print(f"   Total errors: {parsing_results.get('feed_validation', {}).get('total_errors', 0)}")

        # Generate structured output
        structured_output = parser.generate_structured_output(parsing_results)
        print(f"\n📊 Structured Output Summary:")
        print(f"   Overall Status: {structured_output['validation_summary']['status']}")
        print(f"   Has Minimum Media: {'✅ Yes' if structured_output['validation_summary']['has_minimum_media'] else '❌ No'}")
        print(f"   Total Media Types: {len(structured_output['media_inventory']['types'])}")

        # Show module details
        print(f"\n📦 Module Details:")
        for module in structured_output['module_details']:
            print(f"   {module['module_name']}: {module['status']}")

        # Show feed details
        print(f"\n📄 Feed Details:")
        for feed in structured_output['feed_details']:
            print(f"   {feed['feed_name']}: {'✅ Valid' if feed['is_valid'] else '❌ Invalid'} "
                  f"({feed['media_count']} media capabilities)")

        # Test RSS feed parsing
        print(f"\n🌐 Testing RSS feed parsing...")
        test_feed_url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        try:
            rss_results = parser.parse_rss_feed(test_feed_url, max_items=2)
            print(f"   RSS Feed Status: {rss_results.get('status')}")
            print(f"   Items Parsed: {rss_results.get('items_parsed')}")
            print(f"   Items with Media: {rss_results.get('items_with_media')}")

            if rss_results.get('content_items'):
                first_item = rss_results['content_items'][0]
                print(f"   First Item: {first_item.get('title')}")
                print(f"   Has Media: {'✅ Yes' if first_item.get('has_media') else '❌ No'}")

        except Exception as e:
            print(f"   RSS parsing test failed: {str(e)}")

    except Exception as e:
        print(f"❌ Feed parser test failed: {str(e)}")

if __name__ == "__main__":
    main()