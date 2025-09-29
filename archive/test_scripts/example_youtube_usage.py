#!/usr/bin/env python3
"""
Example usage of the YouTube Trailer Scraper

This script demonstrates how to use the YouTube trailer scraper
with your movie data.
"""

import json
from youtube_trailer_scraper import YouTubeTrailerScraper, TrailerResult

def example_single_movie():
    """Example: Search for a single movie trailer"""
    print("=== Single Movie Example ===")
    
    # Initialize scraper (using web scraping method)
    scraper = YouTubeTrailerScraper(method="scrape")
    
    # Search for a trailer
    movie_title = "The Godfather"
    year = 1972
    
    print(f"Searching for trailer: {movie_title} ({year})")
    result = scraper.search_trailer(movie_title, year)
    
    if result.trailer_url:
        print(f"✓ Found trailer: {result.trailer_url}")
        print(f"  Title: {result.title}")
        print(f"  Channel: {result.channel}")
        print(f"  Duration: {result.duration}")
        print(f"  Views: {result.view_count:,}")
        print(f"  Confidence: {result.confidence_score:.2f}")
    else:
        print(f"✗ No trailer found: {result.error}")

def example_api_usage():
    """Example: Using YouTube Data API (requires API key)"""
    print("\n=== API Usage Example ===")
    
    # You need to get a YouTube Data API key from Google Cloud Console
    # https://console.cloud.google.com/apis/credentials
    api_key = "YOUR_YOUTUBE_API_KEY_HERE"
    
    if api_key == "YOUR_YOUTUBE_API_KEY_HERE":
        print("Please set your YouTube API key to use this example")
        return
    
    # Initialize scraper with API
    scraper = YouTubeTrailerScraper(api_key=api_key, method="api")
    
    # Search for multiple movies
    movies = [
        ("Citizen Kane", 1941),
        ("Casablanca", 1942),
        ("The Shawshank Redemption", 1994)
    ]
    
    for title, year in movies:
        print(f"\nSearching for: {title} ({year})")
        result = scraper.search_trailer(title, year)
        
        if result.trailer_url:
            print(f"✓ Found: {result.trailer_url}")
            print(f"  Confidence: {result.confidence_score:.2f}")
        else:
            print(f"✗ Not found: {result.error}")

def example_batch_processing():
    """Example: Process multiple movies from your data"""
    print("\n=== Batch Processing Example ===")
    
    # Load your movie data
    try:
        with open('movie_profiles_merged.json', 'r') as f:
            movie_data = json.load(f)
    except FileNotFoundError:
        print("movie_profiles_merged.json not found. Please run this from the correct directory.")
        return
    
    # Initialize scraper
    scraper = YouTubeTrailerScraper(method="scrape")
    
    # Process first 5 movies as an example
    movies = list(movie_data.items())[:5]
    
    results = []
    for title, data in movies:
        print(f"Processing: {title}")
        
        # Extract year if available in title
        year = None
        if '(' in title and ')' in title:
            import re
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = int(year_match.group(1))
        
        result = scraper.search_trailer(title, year)
        results.append(result)
        
        if result.trailer_url:
            print(f"  ✓ Found: {result.trailer_url}")
        else:
            print(f"  ✗ Not found: {result.error}")
    
    # Summary
    found_count = sum(1 for r in results if r.trailer_url)
    print(f"\nSummary: Found {found_count}/{len(results)} trailers")

def example_integration_with_existing_data():
    """Example: Add trailer links to existing movie data"""
    print("\n=== Integration Example ===")
    
    # Load existing movie data
    try:
        with open('movie_profiles_merged.json', 'r') as f:
            movie_data = json.load(f)
    except FileNotFoundError:
        print("movie_profiles_merged.json not found.")
        return
    
    # Initialize scraper
    scraper = YouTubeTrailerScraper(method="scrape")
    
    # Process a few movies and add trailer data
    sample_movies = list(movie_data.items())[:3]
    
    for title, data in sample_movies:
        print(f"Adding trailer to: {title}")
        
        # Extract year
        year = None
        if '(' in title and ')' in title:
            import re
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = int(year_match.group(1))
        
        # Search for trailer
        result = scraper.search_trailer(title, year)
        
        # Add trailer data to movie
        if result.trailer_url:
            data['trailer_url'] = result.trailer_url
            data['trailer_video_id'] = result.video_id
            data['trailer_title'] = result.title
            data['trailer_channel'] = result.channel
            data['trailer_confidence'] = result.confidence_score
            print(f"  ✓ Added trailer: {result.trailer_url}")
        else:
            data['trailer_error'] = result.error
            print(f"  ✗ No trailer found: {result.error}")
    
    # Save updated data
    output_file = 'movie_profiles_with_trailers_sample.json'
    with open(output_file, 'w') as f:
        json.dump(movie_data, f, indent=2)
    
    print(f"\nUpdated data saved to: {output_file}")

if __name__ == "__main__":
    # Run examples
    example_single_movie()
    example_batch_processing()
    example_integration_with_existing_data()
    
    # Uncomment to test API usage (requires API key)
    # example_api_usage()
