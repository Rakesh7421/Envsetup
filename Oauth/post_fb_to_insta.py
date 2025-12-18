#!/usr/bin/env python3
"""
Post a Facebook post to Instagram by using the Facebook post URL as content
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from publisher.poster import PlatformPoster

def post_fb_to_insta():
    """Post Facebook content to Instagram"""

    print("📢 Facebook to Instagram Poster")
    print("=" * 40)

    try:
        # Initialize poster
        poster = PlatformPoster()
        print("✅ Poster initialized")

        # Load Instagram tokens
        try:
            with open('oauth_tokens_instagram.json', 'r') as f:
                insta_tokens = json.load(f)
            print("✅ Instagram tokens loaded")
        except Exception as e:
            print(f"❌ Could not load Instagram tokens: {str(e)}")
            return

        # Show token info
        print(f"\n📋 Instagram Token Information:")
        print(f"Instagram Account ID: {insta_tokens.get('instagram_account_id')}")
        print(f"Page Access Token: {insta_tokens.get('page_access_token', 'N/A')[:20]}...")

        # Get Facebook post URL from user or use the demo one
        fb_post_url = input("\n🔗 Enter Facebook post URL (or press Enter for demo): ").strip()

        if not fb_post_url:
            # Use the demo post URL
            fb_post_url = "https://facebook.com/865565739968141_122113904289083358"
            print(f"📝 Using demo Facebook post: {fb_post_url}")

        # Create Instagram content from Facebook post
        insta_caption = f"📢 Check out this post on Facebook! 👇\n\n{fb_post_url}\n\n" \
                       "#Facebook #Instagram #CrossPost #SocialMedia"

        print(f"\n📝 Instagram Caption:")
        print(f"\"{insta_caption[:100]}...\"")

        # For Instagram, we need a valid image. Let's use the Facebook post URL as the image
        # This creates a "link in bio" style post pointing to the Facebook content
        image_url = fb_post_url  # Use the Facebook post URL as the "image"

        print(f"\n📸 Posting to Instagram...")
        print(f"📝 Using Facebook post as content: {image_url}")
        print("💡 This creates an Instagram post linking to your Facebook content")

        insta_result = poster.post_to_platform(
            'instagram',
            insta_tokens,
            insta_caption,
            image_url
        )

        if insta_result['success']:
            print(f"✅ Instagram Post Successful!")
            print(f"Container ID: {insta_result.get('container_id')}")
            print(f"💡 Your Instagram post with Facebook link has been created!")
        else:
            print(f"❌ Instagram Post Failed: {insta_result.get('error')}")
            print(f"Message: {insta_result.get('message')}")
            print("\n💡 Instagram Tips:")
            print("   - Use a valid, publicly accessible image URL")
            print("   - Image must meet Facebook's requirements")
            print("   - Try with a real image from a public website")

        print(f"\n🎉 Facebook to Instagram posting completed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    post_fb_to_insta()