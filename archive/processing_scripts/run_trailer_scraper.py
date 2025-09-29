#!/usr/bin/env python3
"""
Quick script to run the YouTube trailer scraper on your movie collection

This script will:
1. Load your existing movie data
2. Search for YouTube trailers
3. Add trailer links to your movie data
4. Save the updated data

Usage:
    python run_trailer_scraper.py
    python run_trailer_scraper.py --limit 10  # Process only first 10 movies
    python run_trailer_scraper.py --method api --api-key YOUR_KEY  # Use YouTube API
"""

import argparse
import json
import logging
from pathlib import Path
from youtube_trailer_scraper import YouTubeTrailerScraper, extract_year_from_title

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='Run YouTube trailer scraper on movie collection')
    parser.add_argument('--input', '-i', default='movie_profiles_merged.json', 
                       help='Input movie data file')
    parser.add_argument('--output', '-o', default='movie_profiles_with_trailers.json',
                       help='Output file for movies with trailers')
    parser.add_argument('--method', '-m', choices=['api', 'scrape'], default='scrape',
                       help='Search method: api (requires API key) or scrape')
    parser.add_argument('--api-key', help='YouTube Data API key (required for api method)')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of movies to process')
    parser.add_argument('--start', type=int, default=0, help='Start from this movie index')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found.")
        print("Available files:")
        for f in Path('.').glob('*.json'):
            print(f"  - {f.name}")
        return
    
    # Load movie data
    print(f"Loading movie data from {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            movie_data = json.load(f)
    except Exception as e:
        print(f"Error loading movie data: {e}")
        return
    
    print(f"Loaded {len(movie_data)} movies")
    
    # Initialize scraper
    print(f"Initializing scraper (method: {args.method})")
    scraper = YouTubeTrailerScraper(api_key=args.api_key, method=args.method)
    
    # Get movies to process
    movies = list(movie_data.items())
    if args.limit:
        movies = movies[args.start:args.start + args.limit]
    else:
        movies = movies[args.start:]
    
    print(f"Processing {len(movies)} movies")
    
    if args.dry_run:
        print("\nDRY RUN - Movies that would be processed:")
        for i, (title, data) in enumerate(movies):
            year = extract_year_from_title(title)
            print(f"{i+1:3d}. {title} ({year})")
        return
    
    # Process movies
    import time
    processed = 0
    found = 0
    
    for i, (title, data) in enumerate(movies):
        print(f"\n[{i+1}/{len(movies)}] Processing: {title}")
        
        # Extract year
        year = extract_year_from_title(title)
        if year:
            print(f"  Year: {year}")
        
        # Search for trailer
        result = scraper.search_trailer(title, year)
        
        # Add results to movie data
        if result.trailer_url:
            data['trailer_url'] = result.trailer_url
            data['trailer_video_id'] = result.video_id
            data['trailer_title'] = result.title
            data['trailer_channel'] = result.channel
            data['trailer_duration'] = result.duration
            data['trailer_view_count'] = result.view_count
            data['trailer_confidence'] = result.confidence_score
            data['trailer_search_method'] = result.search_method
            
            print(f"  ✓ Found trailer: {result.trailer_url}")
            print(f"    Title: {result.title}")
            print(f"    Channel: {result.channel}")
            print(f"    Confidence: {result.confidence_score:.2f}")
            found += 1
        else:
            data['trailer_error'] = result.error
            data['trailer_search_method'] = result.search_method
            print(f"  ✗ No trailer found: {result.error}")
        
        processed += 1
        
        # Save progress every 10 movies
        if processed % 10 == 0:
            print(f"\nSaving progress... ({processed} processed, {found} found)")
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(movie_data, f, indent=2, ensure_ascii=False)
        
        # Rate limiting
        if args.delay > 0:
            time.sleep(args.delay)
    
    # Final save
    print(f"\nSaving final results to {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCompleted!")
    print(f"Processed: {processed} movies")
    print(f"Found trailers: {found} movies")
    print(f"Success rate: {found/processed*100:.1f}%" if processed > 0 else "0%")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
