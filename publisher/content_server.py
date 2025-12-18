#!/usr/bin/env python3
"""
Content Server Module
Manages content creation, storage, and retrieval for the publisher system.
"""

import os
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

class ContentServer:
    """
    Manages content for the publisher system, including storage and retrieval.
    """

    def __init__(self, content_dir: str = 'content', csv_file: str = 'data.csv'):
        """
        Initialize the content server.

        Args:
            content_dir: Directory to store content files
            csv_file: CSV file for tracking posted content
        """
        self.content_dir = content_dir
        self.csv_file = csv_file

        # Create content directory if it doesn't exist
        os.makedirs(self.content_dir, exist_ok=True)

    def create_content(self, title: str, body: str, author: str = 'system', tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new content item.

        Args:
            title: Title of the content
            body: Main content body
            author: Author name
            tags: List of tags/categories

        Returns:
            Dictionary containing the created content
        """
        content_id = self._generate_content_id(title, body)
        timestamp = datetime.now().isoformat()

        content = {
            'id': content_id,
            'title': title,
            'body': body,
            'author': author,
            'tags': tags or [],
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'draft',
            'post_history': []
        }

        return content

    def save_content(self, content: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save content to a file.

        Args:
            content: Content dictionary to save
            filename: Optional filename (will be generated if not provided)

        Returns:
            Path to the saved content file
        """
        if filename is None:
            # Generate filename from title
            title_slug = content['title'].lower().replace(' ', '_')[:50]
            filename = f"{title_slug}_{content['id']}.json"

        filepath = os.path.join(self.content_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            return filepath

        except Exception as e:
            raise Exception(f"Could not save content to {filepath}: {str(e)}")

    def load_content(self, filename: str) -> Dict[str, Any]:
        """
        Load content from a file.

        Args:
            filename: Name of the content file

        Returns:
            Dictionary containing the loaded content
        """
        filepath = os.path.join(self.content_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            raise Exception(f"Could not load content from {filepath}: {str(e)}")

    def list_content(self) -> List[str]:
        """
        List all available content files.

        Returns:
            List of content filenames
        """
        try:
            files = [f for f in os.listdir(self.content_dir) if f.endswith('.json')]
            return sorted(files)
        except Exception as e:
            raise Exception(f"Could not list content: {str(e)}")

    def update_content_status(self, content: Dict[str, Any], status: str, platform: Optional[str] = None, post_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the status of a content item and record post history.

        Args:
            content: Content dictionary to update
            status: New status (draft, scheduled, published, failed)
            platform: Platform where content was posted
            post_result: Result from posting attempt

        Returns:
            Updated content dictionary
        """
        content['status'] = status
        content['updated_at'] = datetime.now().isoformat()

        if platform and post_result:
            post_record = {
                'timestamp': datetime.now().isoformat(),
                'platform': platform,
                'success': post_result.get('success', False),
                'post_id': post_result.get('post_id') or post_result.get('container_id'),
                'error': post_result.get('error')
            }
            content['post_history'].append(post_record)

        return content

    def get_content_for_posting(self, content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Prepare content for posting to a specific platform.

        Args:
            content: Content dictionary
            platform: Target platform

        Returns:
            Dictionary with platform-specific content
        """
        base_content = content['body']

        if platform.lower() == 'facebook':
            # Facebook allows longer posts
            return {
                'content': base_content,
                'image_url': None  # Could be added from content metadata
            }
        elif platform.lower() == 'instagram':
            # Instagram requires an image and shorter caption
            caption = base_content[:2200]  # Instagram caption limit
            return {
                'content': caption,
                'image_url': None  # Required for Instagram
            }
        else:
            return {
                'content': base_content,
                'image_url': None
            }

    def check_content_redundancy(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if content has been posted recently to avoid redundancy.

        Args:
            content: Content dictionary to check

        Returns:
            Dictionary with redundancy status and reference information:
            {
                'is_redundant': True/False,
                'reference': post_id or None,
                'platform': platform_name or None,
                'timestamp': timestamp or None
            }
        """
        try:
            if not os.path.exists(self.csv_file):
                return {
                    'is_redundant': False,
                    'reference': None,
                    'platform': None,
                    'timestamp': None
                }

            content_hash = self._generate_content_hash(content)

            with open(self.csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header

                for row in reader:
                    if len(row) >= 8 and row[2] == str(content_hash):
                        # Content was posted recently, return reference information
                        return {
                            'is_redundant': True,
                            'reference': row[7] if len(row) >= 8 else None,  # post_id
                            'platform': row[1] if len(row) >= 2 else None,  # platform
                            'timestamp': row[0] if len(row) >= 1 else None   # timestamp
                        }

            return {
                'is_redundant': False,
                'reference': None,
                'platform': None,
                'timestamp': None
            }

        except Exception as e:
            print(f"Warning: Could not check content redundancy: {str(e)}")
            return {
                'is_redundant': False,
                'reference': None,
                'platform': None,
                'timestamp': None
            }

    def log_content_post(self, content: Dict[str, Any], platform: str, post_result: Dict[str, Any]) -> None:
        """
        Log content posting to CSV file.

        Args:
            content: Content dictionary
            platform: Platform where content was posted
            post_result: Result from posting attempt
        """
        try:
            content_hash = self._generate_content_hash(content)

            # Check if file exists and has headers
            file_exists = os.path.exists(self.csv_file)

            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)

                # Write header if file doesn't exist
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'platform', 'content_hash', 'content_id',
                        'title', 'success', 'error', 'post_id'
                    ])

                # Write content data
                writer.writerow([
                    datetime.now().isoformat(),
                    platform,
                    content_hash,
                    content.get('id', ''),
                    content.get('title', '')[:50],
                    post_result.get('success', False),
                    post_result.get('error', ''),
                    post_result.get('post_id', '') or post_result.get('container_id', '')
                ])

        except Exception as e:
            print(f"Warning: Could not log content post to CSV: {str(e)}")

    def _generate_content_id(self, title: str, body: str) -> str:
        """
        Generate a unique content ID based on title and body.

        Args:
            title: Content title
            body: Content body

        Returns:
            Generated content ID
        """
        content_str = f"{title}{body}"
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:16]

    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Generate a hash for content redundancy checking.

        Args:
            content: Content dictionary

        Returns:
            Content hash as string
        """
        content_str = f"{content.get('title', '')}{content.get('body', '')}"
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()

    def search_content(self, query: str) -> List[Dict[str, Any]]:
        """
        Search content by query string.

        Args:
            query: Search query

        Returns:
            List of matching content dictionaries
        """
        results = []
        query_lower = query.lower()

        try:
            for filename in self.list_content():
                content = self.load_content(filename)
                content_text = f"{content.get('title', '')} {content.get('body', '')}".lower()

                if query_lower in content_text:
                    results.append(content)

            return results

        except Exception as e:
            print(f"Warning: Could not search content: {str(e)}")
            return []

def main():
    """Test the content server functionality."""
    print("📚 Content Server Test")
    print("=" * 40)

    try:
        content_server = ContentServer()
        print("✅ Content server initialized")

        # Create sample content
        print("\n📝 Creating sample content...")
        sample_content = content_server.create_content(
            title="Test Post from Content Server",
            body="This is a test post created by the content server system. It demonstrates how content can be managed and prepared for posting to various platforms.",
            author="System Test",
            tags=["test", "demo"]
        )
        print(f"Created content: {sample_content['title']}")

        # Save content
        print("\n💾 Saving content...")
        saved_path = content_server.save_content(sample_content)
        print(f"Content saved to: {saved_path}")

        # List content
        print("\n📋 Listing content...")
        content_list = content_server.list_content()
        print(f"Available content files: {content_list}")

        # Load content
        print("\n📖 Loading content...")
        loaded_content = content_server.load_content(content_list[0])
        print(f"Loaded content title: {loaded_content['title']}")

        # Prepare for posting
        print("\n📤 Preparing content for Facebook...")
        fb_content = content_server.get_content_for_posting(loaded_content, 'facebook')
        print(f"Facebook content preview: {fb_content['content'][:100]}...")

        print("\n📸 Preparing content for Instagram...")
        insta_content = content_server.get_content_for_posting(loaded_content, 'instagram')
        print(f"Instagram caption preview: {insta_content['content'][:100]}...")

        # Test redundancy checking
        print("\n🔄 Testing redundancy checking...")
        is_redundant = content_server.check_content_redundancy(loaded_content)
        print(f"Content is redundant: {is_redundant}")

        # Test logging
        print("\n📋 Testing content post logging...")
        sample_result = {
            'success': True,
            'post_id': 'test_post_123',
            'error': None
        }
        content_server.log_content_post(loaded_content, 'test_platform', sample_result)
        print("Content post logged to CSV")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()