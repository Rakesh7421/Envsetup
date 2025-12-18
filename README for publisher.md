# Social Media Publisher - Automated Workflow

## 🚀 Overview

The Social Media Publisher is an automated content publishing system that fetches news content from RSS feeds and publishes it to Facebook and Instagram. The system has been enhanced to **automatically run the publishing workflow** without requiring manual menu selection.

## 📋 Features

### Automated Publishing Workflow
- **Automatic execution**: Runs the complete publishing workflow on startup
- **RSS feed integration**: Fetches content from multiple news sources (NY Times, BBC, The Guardian)
- **Content processing**: Extracts and formats content for social media platforms
- **Multi-platform publishing**: Posts to both Facebook and Instagram
- **Redundancy prevention**: Avoids duplicate content posting
- **Media validation**: Ensures Instagram posts have appropriate images

### Key Components
- **Content Fetcher**: Retrieves and processes RSS feed content
- **Platform Poster**: Handles authentication and posting to social media
- **Content Server**: Manages content lifecycle and logging
- **Media Validator**: Ensures content meets platform requirements

## 🎯 Usage

### Automatic Mode (Default)
The publisher now runs automatically when executed:

```bash
cd publisher
python main.py
```

The system will:
1. Initialize all components
2. Fetch content from configured RSS feeds
3. Process and validate content
4. Publish to available platforms (Facebook/Instagram)
5. Log results and provide summary

### Configuration
- **RSS Feeds**: Configured in `main.py` (lines 29-33)
- **OAuth Tokens**: Requires `oauth_tokens_facebook.json` and `oauth_tokens_instagram.json`
- **Content Limits**: Adjust `max_items` parameter in `main.py` line 525

## 🔧 Setup Requirements

1. **Python 3.7+** with required dependencies
2. **OAuth credentials** for Facebook and Instagram
3. **Valid access tokens** in the publisher directory

## 📊 Workflow Process

1. **Initialization**: Loads platform tokens and validates credentials
2. **Content Fetching**: Retrieves articles from RSS feeds with media requirements
3. **Content Processing**: Creates structured content items with source attribution
4. **Redundancy Check**: Prevents duplicate content posting
5. **Platform Publishing**: Posts to Facebook and Instagram with appropriate formatting
6. **Result Logging**: Saves publishing results and content metadata

## 📈 Sample Output

```
📢 Social Media Publisher
========================================
Automated content publishing system
with RSS feed integration and redundancy prevention

✅ Publisher application initialized

🚀 Running automated publishing workflow...
🚀 Starting publishing workflow...
==================================================
📡 Fetching content from 3 RSS feeds...
🌐 Processing: https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml
✅ Retrieved 1 items from https://rss.nytimes.com/services/xml/rss.xml
📚 Total content items ready: 2

📄 Processing content item 1/2:
   Title: Sample News Article
   Source: www.nytimes.com
📤 Publishing 'Sample News Article' to facebook...
✅ Successfully published to facebook!
📤 Publishing 'Sample News Article' to instagram...
✅ Successfully published to instagram!

🎉 Publishing workflow completed!
   Processed 2 content items
   Generated 2 publishing results

📊 Summary:
   Processed 2 content items

   Item 1: Sample News Article
      Facebook: ✅ Published
      Instagram: ✅ Published

🎉 Publishing workflow completed successfully!
```

## 🛡️ Error Handling

The system includes comprehensive error handling for:
- Invalid OAuth tokens
- Missing media for Instagram posts
- Redundant content detection
- RSS feed parsing errors
- Network connectivity issues

## 🔄 Backward Compatibility

The automated workflow maintains full compatibility with:
- Existing content fetching modules
- Platform posting interfaces
- Content validation systems
- Logging and reporting mechanisms

## 📁 File Structure

```
publisher/
├── main.py                    # Main application (automated workflow)
├── fetch_content.py           # Content fetching module
├── poster.py                  # Platform posting module
├── content_server.py          # Content management
├── media_validator.py         # Media validation
├── enhanced_fetch_content.py  # Enhanced fetching with validation
├── IMPLEMENTATION_SUMMARY.md  # Enhanced fetching documentation
└── README for publisher.md    # This file
```

## 🎉 Summary

The Social Media Publisher now provides a **fully automated publishing workflow** that:

1. **Eliminates manual intervention** - Runs automatically on startup
2. **Maintains all functionality** - Preserves content fetching, processing, and publishing
3. **Provides clear feedback** - Detailed logging and status updates
4. **Handles errors gracefully** - Robust error handling and recovery
5. **Prevents duplicates** - Built-in redundancy detection

The system is production-ready and can be integrated into automated publishing pipelines.