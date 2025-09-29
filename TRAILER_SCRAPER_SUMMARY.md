# YouTube Trailer Scraper - Complete Solution

I've created a comprehensive YouTube trailer scraper system for your movie collection. Here's what's available:

## 🎬 What You Got

### 1. **Main Scraper** (`youtube_trailer_scraper.py`)
- **Full-featured scraper** with YouTube Data API and web scraping support
- **Smart trailer detection** with confidence scoring
- **Rate limiting** and error handling
- **Batch processing** capabilities

### 2. **Simple Scraper** (`simple_trailer_scraper.py`)
- **Lightweight version** focusing on web scraping
- **Easy to use** with minimal dependencies
- **Good for testing** and small batches

### 3. **Manual Trailer Adder** (`manual_trailer_adder.py`)
- **Interactive interface** for manually adding trailer URLs
- **Opens YouTube search** pages automatically
- **Batch import** from text files
- **Most reliable method** for getting accurate results

### 4. **URL Finder** (`trailer_url_finder.py`)
- **Opens YouTube search pages** for all your movies
- **Generates template files** for batch URL entry
- **Helps you find trailers** efficiently

## 🚀 Quick Start Options

### Option 1: Manual Method (Recommended)
```bash
# Step 1: Open YouTube search pages for your movies
python3 trailer_url_finder.py --limit 10

# Step 2: Manually add the URLs you find
python3 manual_trailer_adder.py --input movie_profiles_merged.json
```

### Option 2: Simple Automated Scraping
```bash
# Try automated scraping (may have limited success)
python3 simple_trailer_scraper.py --limit 5 --delay 3
```

### Option 3: YouTube Data API (Best Results)
```bash
# Get a YouTube API key from Google Cloud Console
# Then use the main scraper
python3 youtube_trailer_scraper.py --input movie_profiles_merged.json --method api --api-key YOUR_KEY
```

## 📋 Installation

```bash
# Install basic dependencies
pip3 install beautifulsoup4 requests

# For YouTube Data API (optional but recommended)
pip3 install google-api-python-client

# For rate limiting (optional)
pip3 install ratelimit
```

## 🎯 Recommended Workflow

1. **Start Small**: Test with a few movies first
   ```bash
   python3 trailer_url_finder.py --limit 5
   ```

2. **Use Manual Method**: Most reliable way to get accurate trailer links
   ```bash
   python3 manual_trailer_adder.py --input movie_profiles_merged.json
   ```

3. **Batch Process**: For larger collections, use the template system
   ```bash
   python3 trailer_url_finder.py --generate-template
   # Edit the generated file with URLs
   python3 manual_trailer_adder.py --urls trailer_urls.txt
   ```

## 📊 Output Format

Your movie data will be enhanced with trailer information:

```json
{
  "The Godfather": {
    "title": "The Godfather",
    "trailer_url": "https://www.youtube.com/watch?v=sY1S34973zA",
    "trailer_video_id": "sY1S34973zA",
    "trailer_title": "The Godfather (1972) Official Trailer",
    "trailer_channel": "Paramount Pictures",
    "trailer_confidence": 0.85,
    "trailer_found_at": "2024-01-15T10:30:00"
  }
}
```

## 🔧 Why Multiple Approaches?

- **YouTube Data API**: Most reliable, but requires API key and has quotas
- **Web Scraping**: Free but fragile due to YouTube's changing HTML structure
- **Manual Method**: Most accurate, allows you to verify each trailer is correct

## 💡 Pro Tips

1. **Start with the manual method** - it's the most reliable
2. **Use the URL finder** to open multiple YouTube search pages at once
3. **Generate template files** for batch processing
4. **Test with a small batch** before processing your entire collection
5. **Save progress frequently** - the scripts auto-save every 5-10 movies

## 🎬 Example Usage

```bash
# Find trailers for first 10 movies
python3 trailer_url_finder.py --limit 10

# This opens 10 YouTube search pages
# Find the trailer URLs manually
# Then add them using the manual adder

python3 manual_trailer_adder.py --input movie_profiles_merged.json
# Follow the interactive prompts to add URLs
```

## 📁 Files Created

- `youtube_trailer_scraper.py` - Main comprehensive scraper
- `simple_trailer_scraper.py` - Lightweight scraper
- `manual_trailer_adder.py` - Interactive manual adder
- `trailer_url_finder.py` - URL finder and template generator
- `run_trailer_scraper.py` - Quick runner script
- `example_youtube_usage.py` - Usage examples
- `requirements_youtube.txt` - Dependencies
- `YOUTUBE_TRAILER_SCRAPER_README.md` - Detailed documentation

## 🎯 Next Steps

1. **Try the manual method first** - it's the most reliable
2. **Get a YouTube API key** if you want automated scraping
3. **Process in batches** to avoid overwhelming yourself
4. **Use the template system** for large collections

The manual method is actually quite efficient - you can process 10-20 movies in just a few minutes by copying URLs from the opened YouTube search pages!
