#!/usr/bin/env python3
"""
Create a sample post to test the OAuth and posting functionality
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from publisher.poster import PlatformPoster

def create_sample_post():
    """Create and publish a sample post to demonstrate the functionality"""

    print("📢 Creating Sample Post Demo")
    print("=" * 40)

    try:
        # Initialize poster
        poster = PlatformPoster()
        print("✅ Poster initialized")

        # Load tokens
        fb_tokens = None
        insta_tokens = None

        try:
            with open('oauth_tokens_facebook.json', 'r') as f:
                fb_tokens = json.load(f)
            print("✅ Facebook tokens loaded")
        except Exception as e:
            print(f"❌ Could not load Facebook tokens: {str(e)}")

        try:
            with open('oauth_tokens_instagram.json', 'r') as f:
                insta_tokens = json.load(f)
            print("✅ Instagram tokens loaded")
        except Exception as e:
            print(f"❌ Could not load Instagram tokens: {str(e)}")

        if not fb_tokens and not insta_tokens:
            print("❌ No tokens available for posting")
            return

        # Show token info
        print("\n📋 Token Information:")
        if fb_tokens:
            print(f"Facebook Page ID: {fb_tokens.get('page_id')}")
            print(f"Facebook Page Access Token: {fb_tokens.get('page_access_token', 'N/A')[:20]}...")
        if insta_tokens:
            print(f"Instagram Account ID: {insta_tokens.get('instagram_account_id')}")
            print(f"Instagram Page Access Token: {insta_tokens.get('page_access_token', 'N/A')[:20]}...")

        # Create sample content
        sample_content = "🚀 Test post from the Enhanced OAuth System! 🎉\n\n" \
                        "This post demonstrates that the OAuth flow is working correctly " \
                        "and we can successfully post to social media platforms.\n\n" \
                        "#OAuth #FacebookAPI #InstagramAPI #Automation"

        print(f"\n📝 Sample Content:")
        print(f"\"{sample_content[:100]}...\"")

        # Test Facebook posting
        if fb_tokens:
            print(f"\n📘 Posting to Facebook...")
            fb_result = poster.post_to_platform(
                'facebook',
                fb_tokens,
                sample_content,
                "https://www.example.com/sample-image.jpg"  # Using example image
            )

            if fb_result['success']:
                print(f"✅ Facebook Post Successful!")
                print(f"Post ID: {fb_result.get('post_id')}")
                print(f"Post URL: {fb_result.get('post_url')}")
            else:
                print(f"❌ Facebook Post Failed: {fb_result.get('error')}")
                print(f"Message: {fb_result.get('message')}")

        # Test Instagram posting
        if insta_tokens:
            print(f"\n📸 Posting to Instagram...")
            # Note: Instagram requires a valid image URL that Facebook can access
            # Using a placeholder that might not work, but demonstrates the flow
            insta_result = poster.post_to_platform(
                'instagram',
                insta_tokens,
                "Test Instagram post! 🌟 #OAuth #Testing",
                "https://www.example.com/sample-image.jpg"
            )

            if insta_result['success']:
                print(f"✅ Instagram Post Successful!")
                print(f"Container ID: {insta_result.get('container_id')}")
            else:
                print(f"❌ Instagram Post Failed: {insta_result.get('error')}")
                print(f"Message: {insta_result.get('message')}")
                print("ℹ️  Note: Instagram requires a valid, accessible image URL")

        print(f"\n🎉 Sample post demo completed!")
        print("💡 Check your Facebook page and Instagram account for the test posts.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_post()