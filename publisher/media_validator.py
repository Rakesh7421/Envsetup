#!/usr/bin/env python3
"""
Media Validation Module
Validates content feeds for media requirements and extracts structured metadata.
"""

import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import re
from datetime import datetime
import importlib.util
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MediaValidator:
    """
    Validates content feeds for media requirements and extracts structured metadata.
    """

    def __init__(self):
        """
        Initialize the media validator.
        """
        self.supported_media_types = ['image', 'video']
        self.supported_image_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
        self.supported_video_formats = ['mp4', 'webm', 'mov', 'avi', 'mkv']

    def validate_feed_directory(self, feed_directory: str = 'publisher/fetch_contentt') -> Dict[str, Any]:
        """
        Validate all feed modules in the specified directory.

        Args:
            feed_directory: Directory containing feed modules

        Returns:
            Dictionary with validation results for all feeds
        """
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'feed_directory': feed_directory,
            'feeds_validated': [],
            'total_media_count': 0,
            'total_errors': 0,
            'total_warnings': 0
        }

        try:
            # Get all Python files in the directory
            feed_files = []
            for filename in os.listdir(feed_directory):
                if filename.endswith('.py') and not filename.startswith('__'):
                    feed_files.append(filename)

            logger.info(f"Found {len(feed_files)} feed modules to validate")

            # Validate each feed module
            for feed_file in feed_files:
                feed_result = self._validate_single_feed_module(feed_directory, feed_file)
                validation_results['feeds_validated'].append(feed_result)

                # Update totals
                validation_results['total_media_count'] += feed_result.get('media_count', 0)
                validation_results['total_errors'] += len(feed_result.get('errors', []))
                validation_results['total_warnings'] += len(feed_result.get('warnings', []))

            # Determine overall validation status
            has_errors = validation_results['total_errors'] > 0
            has_media = validation_results['total_media_count'] > 0

            validation_results['validation_status'] = (
                'SUCCESS' if has_media and not has_errors else
                'PARTIAL' if has_media and has_errors else
                'FAILURE'
            )

            return validation_results

        except Exception as e:
            logger.error(f"Error validating feed directory: {str(e)}")
            validation_results['validation_status'] = 'ERROR'
            validation_results['errors'] = [f"Validation failed: {str(e)}"]
            return validation_results

    def _validate_single_feed_module(self, feed_directory: str, feed_file: str) -> Dict[str, Any]:
        """
        Validate a single feed module.

        Args:
            feed_directory: Directory containing the feed module
            feed_file: Filename of the feed module

        Returns:
            Dictionary with validation results for the feed
        """
        feed_result = {
            'feed_name': feed_file.replace('.py', ''),
            'module_path': os.path.join(feed_directory, feed_file),
            'validation_timestamp': datetime.now().isoformat(),
            'is_valid': False,
            'has_media_support': False,
            'media_count': 0,
            'media_types': [],
            'errors': [],
            'warnings': [],
            'metadata': {}
        }

        try:
            # Import the feed module dynamically
            module_path = os.path.join(feed_directory, feed_file)
            spec = importlib.util.spec_from_file_location(feed_result['feed_name'], module_path)
            if spec and spec.loader:
                feed_module = importlib.util.module_from_spec(spec)
                sys.modules[feed_result['feed_name']] = feed_module
                spec.loader.exec_module(feed_module)

                # Analyze the feed module
                feed_result = self._analyze_feed_module(feed_module, feed_result)

            else:
                feed_result['errors'].append(f"Could not load module: {feed_file}")
                logger.error(f"Could not load feed module: {feed_file}")

        except Exception as e:
            feed_result['errors'].append(f"Module validation error: {str(e)}")
            logger.error(f"Error validating feed module {feed_file}: {str(e)}")

        # Determine overall validation status
        feed_result['is_valid'] = (
            len(feed_result['errors']) == 0 and
            feed_result['has_media_support'] and
            feed_result['media_count'] > 0
        )

        return feed_result

    def _analyze_feed_module(self, feed_module, feed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a loaded feed module for media capabilities.

        Args:
            feed_module: Loaded feed module
            feed_result: Current validation result dictionary

        Returns:
            Updated validation result dictionary
        """
        try:
            # Check for media-related methods and attributes
            module_attrs = dir(feed_module)

            # Look for media detection methods
            has_media_methods = any(attr.lower().find('media') >= 0 for attr in module_attrs)
            has_content_methods = any(attr.lower().find('content') >= 0 for attr in module_attrs)

            if has_media_methods or has_content_methods:
                feed_result['has_media_support'] = True

            # Extract module metadata
            feed_result['metadata'] = self._extract_module_metadata(feed_module)

            # Check for specific media handling capabilities
            if hasattr(feed_module, 'fetch_rss_feed'):
                feed_result['media_types'].extend(['rss', 'xml'])
                feed_result['media_count'] += 1

            if hasattr(feed_module, 'fetch_visualping_content'):
                feed_result['media_types'].extend(['visualping', 'visual'])
                feed_result['media_count'] += 1

            # Look for media extraction methods
            if hasattr(feed_module, '_has_media_content'):
                feed_result['media_types'].append('media_detection')
                feed_result['media_count'] += 1

            if hasattr(feed_module, '_extract_image_url'):
                feed_result['media_types'].append('image_extraction')
                feed_result['media_count'] += 1

            # Check for URL validation
            if hasattr(feed_module, 'validate_rss_url'):
                feed_result['media_types'].append('url_validation')
                feed_result['media_count'] += 1

            logger.info(f"Analyzed {feed_result['feed_name']}: found {feed_result['media_count']} media capabilities")

        except Exception as e:
            feed_result['errors'].append(f"Module analysis error: {str(e)}")
            logger.error(f"Error analyzing feed module: {str(e)}")

        return feed_result

    def _extract_module_metadata(self, feed_module) -> Dict[str, Any]:
        """
        Extract metadata from a feed module.

        Args:
            feed_module: Loaded feed module

        Returns:
            Dictionary with module metadata
        """
        metadata = {
            'module_name': getattr(feed_module, '__name__', 'unknown'),
            'docstring': getattr(feed_module, '__doc__', '').strip() if hasattr(feed_module, '__doc__') else '',
            'classes': [],
            'functions': [],
            'imports': []
        }

        try:
            # Extract classes
            for attr_name in dir(feed_module):
                attr = getattr(feed_module, attr_name)
                if inspect.isclass(attr) and attr.__module__ == feed_module.__name__:
                    metadata['classes'].append(attr_name)

            # Extract functions
            for attr_name in dir(feed_module):
                attr = getattr(feed_module, attr_name)
                if inspect.isfunction(attr) and attr.__module__ == feed_module.__name__:
                    metadata['functions'].append(attr_name)

            # Extract imports (approximate)
            source_lines = []
            try:
                with open(feed_module.__file__, 'r') as f:
                    source_lines = f.readlines()
            except:
                pass

            for line in source_lines[:20]:  # Check first 20 lines for imports
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    metadata['imports'].append(line.strip())

        except Exception as e:
            logger.warning(f"Could not extract full metadata: {str(e)}")

        return metadata

    def validate_media_url(self, media_url: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Validate that a media URL is accessible and returns valid content.

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
                    if self._is_valid_media_content_type(validation_result['content_type']):
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

    def _is_valid_media_content_type(self, content_type: str) -> bool:
        """
        Check if content type is valid for media.

        Args:
            content_type: Content type string

        Returns:
            True if valid media content type, False otherwise
        """
        if not content_type:
            return False

        content_type = content_type.lower()

        # Check for image types
        if content_type.startswith('image/'):
            return True

        # Check for video types
        if content_type.startswith('video/'):
            return True

        # Check specific formats
        for img_format in self.supported_image_formats:
            if f'image/{img_format}' in content_type:
                return True

        for video_format in self.supported_video_formats:
            if f'video/{video_format}' in content_type:
                return True

        return False

    def extract_media_from_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract media information from a content item.

        Args:
            content_item: Content item dictionary

        Returns:
            Dictionary with extracted media information
        """
        media_info = {
            'images': [],
            'videos': [],
            'total_media_count': 0,
            'has_valid_media': False,
            'validation_results': []
        }

        try:
            # Extract from raw entry if available
            raw_entry = content_item.get('raw_entry', {})

            # Extract images from media_content
            if hasattr(raw_entry, 'media_content'):
                for media in raw_entry.media_content:
                    if media.get('medium') == 'image':
                        image_info = self._extract_image_info(media)
                        if image_info:
                            media_info['images'].append(image_info)
                            media_info['total_media_count'] += 1

            # Extract videos from media_content
            if hasattr(raw_entry, 'media_content'):
                for media in raw_entry.media_content:
                    if media.get('medium') == 'video':
                        video_info = self._extract_video_info(media)
                        if video_info:
                            media_info['videos'].append(video_info)
                            media_info['total_media_count'] += 1

            # Extract from media_thumbnail
            if hasattr(raw_entry, 'media_thumbnail'):
                for media in raw_entry.media_thumbnail:
                    if media.get('url'):
                        image_info = self._extract_image_info(media)
                        if image_info:
                            media_info['images'].append(image_info)
                            media_info['total_media_count'] += 1

            # Extract from enclosures
            if hasattr(raw_entry, 'enclosures'):
                for enclosure in raw_entry.enclosures:
                    enclosure_type = enclosure.get('type', '').lower()
                    if enclosure_type.startswith('image/'):
                        image_info = {
                            'url': enclosure.get('href'),
                            'type': enclosure_type,
                            'length': enclosure.get('length')
                        }
                        media_info['images'].append(image_info)
                        media_info['total_media_count'] += 1
                    elif enclosure_type.startswith('video/'):
                        video_info = {
                            'url': enclosure.get('href'),
                            'type': enclosure_type,
                            'length': enclosure.get('length')
                        }
                        media_info['videos'].append(video_info)
                        media_info['total_media_count'] += 1

            # Extract from content HTML
            content_html = content_item.get('content', '')
            if content_html:
                # Extract image URLs from HTML
                img_urls = self._extract_img_urls_from_html(content_html)
                for img_url in img_urls:
                    image_info = {
                        'url': img_url,
                        'source': 'html_content'
                    }
                    media_info['images'].append(image_info)
                    media_info['total_media_count'] += 1

                # Extract video URLs from HTML
                video_urls = self._extract_video_urls_from_html(content_html)
                for video_url in video_urls:
                    video_info = {
                        'url': video_url,
                        'source': 'html_content'
                    }
                    media_info['videos'].append(video_info)
                    media_info['total_media_count'] += 1

            # Validate extracted media URLs
            media_info['has_valid_media'] = media_info['total_media_count'] > 0
            media_info['validation_results'] = self._validate_extracted_media(media_info)

        except Exception as e:
            logger.error(f"Error extracting media from content: {str(e)}")
            media_info['error'] = str(e)

        return media_info

    def _extract_image_info(self, media_item: Any) -> Optional[Dict[str, Any]]:
        """
        Extract image information from a media item.

        Args:
            media_item: Media item from feed

        Returns:
            Dictionary with image information or None
        """
        try:
            image_info = {
                'url': media_item.get('url'),
                'type': media_item.get('type'),
                'medium': media_item.get('medium'),
                'width': media_item.get('width'),
                'height': media_item.get('height')
            }

            # Clean up and validate
            if not image_info['url']:
                return None

            if not image_info['type'] and image_info['url']:
                # Try to infer type from URL
                image_info['type'] = self._infer_media_type_from_url(image_info['url'])

            return image_info

        except Exception as e:
            logger.warning(f"Could not extract image info: {str(e)}")
            return None

    def _extract_video_info(self, media_item: Any) -> Optional[Dict[str, Any]]:
        """
        Extract video information from a media item.

        Args:
            media_item: Media item from feed

        Returns:
            Dictionary with video information or None
        """
        try:
            video_info = {
                'url': media_item.get('url'),
                'type': media_item.get('type'),
                'medium': media_item.get('medium'),
                'width': media_item.get('width'),
                'height': media_item.get('height'),
                'duration': media_item.get('duration')
            }

            # Clean up and validate
            if not video_info['url']:
                return None

            if not video_info['type'] and video_info['url']:
                # Try to infer type from URL
                video_info['type'] = self._infer_media_type_from_url(video_info['url'])

            return video_info

        except Exception as e:
            logger.warning(f"Could not extract video info: {str(e)}")
            return None

    def _extract_img_urls_from_html(self, html_content: str) -> List[str]:
        """
        Extract image URLs from HTML content.

        Args:
            html_content: HTML content string

        Returns:
            List of image URLs
        """
        img_urls = []
        try:
            # Simple regex to find img tags and extract src attributes
            img_pattern = r'<img[^>]+src="([^"]+)"'
            matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            img_urls.extend(matches)

            # Also look for data-src attributes
            data_src_pattern = r'<img[^>]+data-src="([^"]+)"'
            data_matches = re.findall(data_src_pattern, html_content, re.IGNORECASE)
            img_urls.extend(data_matches)

        except Exception as e:
            logger.warning(f"Could not extract image URLs from HTML: {str(e)}")

        return img_urls

    def _extract_video_urls_from_html(self, html_content: str) -> List[str]:
        """
        Extract video URLs from HTML content.

        Args:
            html_content: HTML content string

        Returns:
            List of video URLs
        """
        video_urls = []
        try:
            # Simple regex to find video tags and extract src attributes
            video_pattern = r'<video[^>]+src="([^"]+)"'
            matches = re.findall(video_pattern, html_content, re.IGNORECASE)
            video_urls.extend(matches)

            # Look for source tags within video tags
            source_pattern = r'<source[^>]+src="([^"]+)"'
            source_matches = re.findall(source_pattern, html_content, re.IGNORECASE)
            video_urls.extend(source_matches)

            # Look for iframe embeds (YouTube, Vimeo, etc.)
            iframe_pattern = r'<iframe[^>]+src="([^"]+)"'
            iframe_matches = re.findall(iframe_pattern, html_content, re.IGNORECASE)
            for iframe_url in iframe_matches:
                if any(domain in iframe_url.lower() for domain in ['youtube', 'vimeo', 'dailymotion']):
                    video_urls.append(iframe_url)

        except Exception as e:
            logger.warning(f"Could not extract video URLs from HTML: {str(e)}")

        return video_urls

    def _validate_extracted_media(self, media_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate extracted media URLs.

        Args:
            media_info: Media information dictionary

        Returns:
            List of validation results for each media item
        """
        validation_results = []

        try:
            # Validate images
            for image in media_info['images']:
                if image.get('url'):
                    validation = self.validate_media_url(image['url'])
                    validation['media_type'] = 'image'
                    validation_results.append(validation)

            # Validate videos
            for video in media_info['videos']:
                if video.get('url'):
                    validation = self.validate_media_url(video['url'])
                    validation['media_type'] = 'video'
                    validation_results.append(validation)

        except Exception as e:
            logger.error(f"Error validating extracted media: {str(e)}")

        return validation_results

    def _infer_media_type_from_url(self, url: str) -> str:
        """
        Infer media type from URL extension.

        Args:
            url: Media URL

        Returns:
            Inferred media type
        """
        try:
            # Extract file extension
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            # Check for image extensions
            for ext in self.supported_image_formats:
                if path.endswith(f'.{ext}'):
                    return f'image/{ext}'

            # Check for video extensions
            for ext in self.supported_video_formats:
                if path.endswith(f'.{ext}'):
                    return f'video/{ext}'

            # Check for common patterns
            if any(domain in url.lower() for domain in ['youtube', 'vimeo', 'dailymotion']):
                return 'video/embed'

            return 'application/octet-stream'

        except Exception as e:
            logger.warning(f"Could not infer media type from URL: {str(e)}")
            return 'unknown/unknown'

    def generate_structured_output(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured output from validation results.

        Args:
            validation_results: Validation results dictionary

        Returns:
            Structured output dictionary
        """
        structured_output = {
            'validation_summary': {
                'timestamp': validation_results.get('timestamp'),
                'status': validation_results.get('validation_status', 'UNKNOWN'),
                'total_feeds': len(validation_results.get('feeds_validated', [])),
                'total_media_count': validation_results.get('total_media_count', 0),
                'total_errors': validation_results.get('total_errors', 0),
                'total_warnings': validation_results.get('total_warnings', 0),
                'has_minimum_media': validation_results.get('total_media_count', 0) > 0
            },
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
            # Process each feed
            for feed_result in validation_results.get('feeds_validated', []):
                feed_detail = {
                    'feed_name': feed_result.get('feed_name'),
                    'is_valid': feed_result.get('is_valid', False),
                    'has_media_support': feed_result.get('has_media_support', False),
                    'media_count': feed_result.get('media_count', 0),
                    'media_types': feed_result.get('media_types', []),
                    'warnings': feed_result.get('warnings', []),
                    'errors': feed_result.get('errors', [])
                }

                structured_output['feed_details'].append(feed_detail)

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

            # Collect all warnings and errors
            for feed_result in validation_results.get('feeds_validated', []):
                structured_output['warnings'].extend(feed_result.get('warnings', []))
                structured_output['errors'].extend(feed_result.get('errors', []))

        except Exception as e:
            logger.error(f"Error generating structured output: {str(e)}")
            structured_output['errors'].append(f"Output generation error: {str(e)}")

        return structured_output

# Import inspect for metadata extraction
import inspect

def main():
    """Test the media validator functionality."""
    print("🔍 Media Validator Test")
    print("=" * 40)

    try:
        validator = MediaValidator()

        # Test feed directory validation
        print("\n📁 Testing feed directory validation...")
        validation_results = validator.validate_feed_directory()

        print(f"✅ Validation completed with status: {validation_results.get('validation_status')}")
        print(f"   Total feeds validated: {len(validation_results.get('feeds_validated', []))}")
        print(f"   Total media count: {validation_results.get('total_media_count')}")
        print(f"   Total errors: {validation_results.get('total_errors')}")
        print(f"   Total warnings: {validation_results.get('total_warnings')}")

        # Generate structured output
        structured_output = validator.generate_structured_output(validation_results)
        print(f"\n📊 Structured Output Summary:")
        print(f"   Validation Status: {structured_output['validation_summary']['status']}")
        print(f"   Has Minimum Media: {'✅ Yes' if structured_output['validation_summary']['has_minimum_media'] else '❌ No'}")
        print(f"   Total Media Types: {len(structured_output['media_inventory']['types'])}")

        # Show feed details
        print(f"\n📄 Feed Details:")
        for feed in structured_output['feed_details']:
            print(f"   {feed['feed_name']}: {'✅ Valid' if feed['is_valid'] else '❌ Invalid'} "
                  f"({feed['media_count']} media capabilities)")

        # Test media URL validation
        print(f"\n🔗 Testing media URL validation...")
        test_url = "https://via.placeholder.com/350x150"
        url_validation = validator.validate_media_url(test_url)
        print(f"   Test URL: {test_url}")
        print(f"   Is Valid: {'✅ Yes' if url_validation['is_valid'] else '❌ No'}")
        print(f"   Status: {url_validation.get('status_code')}")
        print(f"   Content Type: {url_validation.get('content_type')}")

    except Exception as e:
        print(f"❌ Media validator test failed: {str(e)}")

if __name__ == "__main__":
    main()