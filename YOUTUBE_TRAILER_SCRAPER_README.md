t# YouTube Trailer Scraper

A comprehensive tool to find and extract YouTube trailer links for movies in your collection.

## Features

- **Dual Search Methods**: YouTube Data API (recommended) and web scraping fallback
- **Smart Matching**: Intelligent trailer detection with confidence scoring
- **Rate Limiting**: Built-in rate limiting to respect YouTube's terms of service
- **Batch Processing**: Process entire movie collections efficiently
- **Progress Tracking**: Save progress and resume interrupted operations
- **Error Handling**: Robust error handling and logging

## Installation

1. Install required dependencies:
```bash
pip install -r requirements_youtube.txt
```

2. (Optional) Get a YouTube Data API key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project or select existing one
   - Enable the YouTube Data API v3
   - Create credentials (API key)
   - Copy the API key for use with the scraper

## Quick Start

### Method 1: Web Scraping (No API Key Required)

```bash
# Process all movies with web scraping
python run_trailer_scraper.py

# Process only first 10 movies
python run_trailer_scraper.py --limit 10

# Process with custom delay between requests
python run_trailer_scraper.py --delay 3.0
```

### Method 2: YouTube Data API (Recommended)

```bash
# Using YouTube Data API (requires API key)
python run_trailer_scraper.py --method api --api-key YOUR_YOUTUBE_API_KEY

# Process specific range of movies
python run_trailer_scraper.py --method api --api-key YOUR_KEY --start 100 --limit 50
```

## Advanced Usage

### Using the Main Scraper Script

```bash
# Basic usage
python youtube_trailer_scraper.py --input movie_profiles_merged.json --output movies_with_trailers.json

# With YouTube API
python youtube_trailer_scraper.py --input movie_profiles_merged.json --method api --api-key YOUR_KEY

# Process specific range
python youtube_trailer_scraper.py --input movie_profiles_merged.json --start-index 50 --limit 25

# Dry run to see what would be processed
python youtube_trailer_scraper.py --input movie_profiles_merged.json --dry-run
```

### Programmatic Usage

```python
from youtube_trailer_scraper import YouTubeTrailerScraper

# Initialize scraper
scraper = YouTubeTrailerScraper(method="scrape")  # or method="api" with api_key

# Search for a single movie
result = scraper.search_trailer("The Godfather", 1972)

if result.trailer_url:
    print(f"Found trailer: {result.trailer_url}")
    print(f"Confidence: {result.confidence_score}")
else:
    print(f"No trailer found: {result.error}")
```

## Output Format

The scraper adds the following fields to your movie data:

```json
{
  "movie_title": {
    "title": "The Godfather",
    "trailer_url": "https://www.youtube.com/watch?v=sY1S34973zA",
    "trailer_video_id": "sY1S34973zA",
    "trailer_title": "The Godfather (1972) Official Trailer",
    "trailer_channel": "Paramount Pictures",
    "trailer_duration": "PT2M30S",
    "trailer_view_count": 15000000,
    "trailer_confidence": 0.85,
    "trailer_search_method": "api",
    "trailer_found_at": "2024-01-15T10:30:00"
  }
}
```

## Configuration Options

### Command Line Arguments

- `--input, -i`: Input JSON file with movie data
- `--output, -o`: Output JSON file (default: input_with_trailers.json)
- `--method, -m`: Search method (`api` or `scrape`)
- `--api-key`: YouTube Data API key (required for API method)
- `--limit, -l`: Limit number of movies to process
- `--start-index`: Start processing from this index
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--dry-run`: Show what would be processed without making requests

### Environment Variables

You can set your YouTube API key as an environment variable:

```bash
export YOUTUBE_API_KEY="your_api_key_here"
python run_trailer_scraper.py --method api
```

## Trailer Detection Algorithm

The scraper uses a sophisticated algorithm to find the best trailer match:

1. **Search Query Optimization**: Builds optimized search queries with movie title, year, and "trailer" keyword
2. **Confidence Scoring**: Calculates confidence scores based on:
   - Title similarity
   - Presence of trailer keywords
   - Year matching
   - Absence of negative keywords (review, analysis, etc.)
3. **Quality Filtering**: Filters out non-trailer content like reviews and analysis videos
4. **Best Match Selection**: Selects the highest confidence match above threshold

## Rate Limiting

The scraper includes built-in rate limiting to respect YouTube's terms of service:

- **API Method**: 100 requests per 100 seconds (YouTube API quota)
- **Scraping Method**: 10 requests per 60 seconds (conservative approach)
- **Configurable Delays**: Custom delays between requests

## Error Handling

The scraper handles various error conditions:

- Network timeouts and connection errors
- YouTube API quota exceeded
- Invalid movie titles or missing data
- HTML parsing errors (scraping method)
- Rate limiting and retry logic

## Logging

All operations are logged to both console and `youtube_scraper.log` file:

- Search progress and results
- Error messages and warnings
- Performance metrics
- API quota usage

## Examples

See `example_youtube_usage.py` for comprehensive usage examples including:

- Single movie search
- Batch processing
- API integration
- Data integration with existing movie collections

## Troubleshooting

### Common Issues

1. **"No videos found"**: 
   - Try different search terms
   - Check if movie title is correct
   - Some very old or obscure movies may not have trailers

2. **API quota exceeded**:
   - Wait for quota reset (daily)
   - Use scraping method as fallback
   - Reduce batch size

3. **Scraping errors**:
   - YouTube may have changed their HTML structure
   - Try using API method instead
   - Increase delay between requests

4. **Low confidence scores**:
   - Check movie title format
   - Ensure year is correct
   - Some movies may have poor trailer matches

### Getting Help

- Check the log file `youtube_scraper.log` for detailed error messages
- Use `--dry-run` to test without making actual requests
- Start with a small batch (`--limit 5`) to test your setup

## Performance Tips

1. **Use YouTube Data API**: Much more reliable and faster than scraping
2. **Batch Processing**: Process movies in batches to save progress
3. **Appropriate Delays**: Use 2-3 second delays for scraping, 1 second for API
4. **Resume Capability**: Use `--start-index` to resume interrupted operations

## Legal Considerations

- Respect YouTube's Terms of Service
- Use appropriate rate limiting
- Consider YouTube's API quotas
- Be mindful of copyright when using trailer content

## Contributing

Feel free to improve the scraper by:

- Adding new search methods
- Improving trailer detection algorithms
- Adding support for other video platforms
- Enhancing error handling and logging
