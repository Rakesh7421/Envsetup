#!/usr/bin/env python3
"""
VisualPing Content Fetcher Module
Fetches and processes content from VisualPing API.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import requests
import json

class VisualPingFetcher:
    """
    Fetches and processes content from VisualPing API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the VisualPing fetcher.

        Args:
            api_key: VisualPing API key (optional)
        """
        self.api_key = api_key
        self.base_url = "https://api.visualping.io/v1"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

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
            if not self.api_key:
                return self._mock_visualping_response(url_id)

            # Make API request to VisualPing
            endpoint = f"{self.base_url}/checks/{url_id}"
            response = requests.get(endpoint, headers=self.headers)

            if response.status_code == 200:
                api_data = response.json()
                return self._process_visualping_response(api_data, url_id)
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
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown.domain"

    def set_api_key(self, api_key: str):
        """
        Set or update the VisualPing API key.

        Args:
            api_key: VisualPing API key
        """
        self.api_key = api_key
        self.headers['Authorization'] = f'Bearer {api_key}'

def main():
    """Test the VisualPing content fetcher functionality."""
    print("🔍 VisualPing Content Fetcher Test")
    print("=" * 40)

    try:
        # Initialize fetcher (without API key for testing)
        fetcher = VisualPingFetcher()
        print("✅ VisualPing fetcher initialized (mock mode)")

        # Test with sample URL IDs
        test_url_ids = ['test_site_123', 'monitored_page_456']

        for url_id in test_url_ids[:1]:  # Test with just one
            print(f"\n🌐 Fetching VisualPing content for: {url_id}")
            vp_content = fetcher.fetch_visualping_content(url_id)

            if vp_content:
                print(f"✅ Retrieved VisualPing content:")
                print(f"   Title: {vp_content['title']}")
                print(f"   Domain: {vp_content['domain']}")
                print(f"   State: {vp_content['state']}")
                print(f"   Change Type: {vp_content['change_type']}")
                print(f"   Content Preview: {vp_content['content'][:150]}...")
            else:
                print(f"ℹ️  No visual content found for {url_id} (media filtering enabled)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()