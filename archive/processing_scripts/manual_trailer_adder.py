#!/usr/bin/env python3
"""
Manual Trailer Link Adder

This script helps you manually add YouTube trailer links to your movie collection.
It provides an interactive interface to search and add trailers one by one.

Usage:
    python manual_trailer_adder.py --input movie_profiles_merged.json
"""

import json
import argparse
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import re

def extract_year_from_title(title: str) -> Optional[int]:
    """Extract year from movie title if present"""
    year_match = re.search(r'\((\d{4})\)$', title)
    if year_match:
        return int(year_match.group(1))
    
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if year_match:
        return int(year_match.group(0))
    
    return None

def build_youtube_search_url(movie_title: str, year: Optional[int] = None) -> str:
    """Build YouTube search URL for a movie"""
    query_parts = [movie_title]
    if year:
        query_parts.append(str(year))
    query_parts.append("trailer")
    
    query = " ".join(query_parts)
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a valid YouTube video URL"""
    return extract_video_id_from_url(url) is not None

def interactive_trailer_adder(movie_data: Dict[str, Any], output_file: str):
    """Interactive interface for adding trailer links"""
    
    movies = list(movie_data.items())
    processed = 0
    added = 0
    
    print(f"\n=== Manual Trailer Link Adder ===")
    print(f"Total movies: {len(movies)}")
    print(f"Commands: 'skip', 'quit', 'save', 'open' (to open YouTube search)")
    print("=" * 50)
    
    for i, (title, data) in enumerate(movies):
        # Skip if already has trailer
        if 'trailer_url' in data and data['trailer_url']:
            continue
        
        year = extract_year_from_title(title)
        year_str = f" ({year})" if year else ""
        
        print(f"\n[{i+1}/{len(movies)}] {title}{year_str}")
        
        # Show current data
        if 'trailer_url' in data:
            print(f"Current trailer: {data['trailer_url']}")
        
        # Get user input
        while True:
            user_input = input("Enter YouTube URL, 'skip', 'open', 'save', or 'quit': ").strip()
            
            if user_input.lower() == 'quit':
                print("Exiting...")
                return
            
            elif user_input.lower() == 'save':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(movie_data, f, indent=2, ensure_ascii=False)
                print(f"Progress saved to {output_file}")
                continue
            
            elif user_input.lower() == 'skip':
                print("Skipped")
                break
            
            elif user_input.lower() == 'open':
                search_url = build_youtube_search_url(title, year)
                print(f"Opening YouTube search: {search_url}")
                webbrowser.open(search_url)
                continue
            
            elif user_input.startswith('http'):
                # Validate YouTube URL
                if not validate_youtube_url(user_input):
                    print("Invalid YouTube URL. Please enter a valid YouTube video URL.")
                    continue
                
                # Extract video ID
                video_id = extract_video_id_from_url(user_input)
                
                # Add trailer data
                data['trailer_url'] = user_input
                data['trailer_video_id'] = video_id
                data['trailer_added_manually'] = True
                data['trailer_added_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"✓ Added trailer: {user_input}")
                added += 1
                break
            
            else:
                print("Invalid input. Please enter a YouTube URL, 'skip', 'open', 'save', or 'quit'.")
        
        processed += 1
        
        # Auto-save every 10 movies
        if processed % 10 == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(movie_data, f, indent=2, ensure_ascii=False)
            print(f"Auto-saved progress ({processed} processed, {added} added)")
    
    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Completed ===")
    print(f"Processed: {processed} movies")
    print(f"Added trailers: {added} movies")
    print(f"Results saved to: {output_file}")

def batch_url_adder(movie_data: Dict[str, Any], urls_file: str, output_file: str):
    """Add trailer URLs from a text file"""
    
    # Load URLs from file
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"URLs file '{urls_file}' not found.")
        return
    
    # Parse URLs (format: "Movie Title: YouTube URL")
    url_mapping = {}
    for line in lines:
        line = line.strip()
        if ':' in line and 'http' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                url = parts[1].strip()
                if validate_youtube_url(url):
                    url_mapping[title] = url
    
    print(f"Loaded {len(url_mapping)} URLs from {urls_file}")
    
    # Add URLs to movie data
    added = 0
    for title, data in movie_data.items():
        if title in url_mapping:
            url = url_mapping[title]
            video_id = extract_video_id_from_url(url)
            
            data['trailer_url'] = url
            data['trailer_video_id'] = video_id
            data['trailer_added_batch'] = True
            data['trailer_added_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"✓ Added trailer for '{title}': {url}")
            added += 1
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nAdded {added} trailers from batch file")
    print(f"Results saved to: {output_file}")

def main():
    import time
    
    parser = argparse.ArgumentParser(description='Manually add YouTube trailer links to movies')
    parser.add_argument('--input', '-i', default='movie_profiles_merged.json', 
                       help='Input movie data file')
    parser.add_argument('--output', '-o', default='movies_with_trailers_manual.json',
                       help='Output file for movies with trailers')
    parser.add_argument('--urls', help='Text file with movie titles and URLs (format: "Title: URL")')
    parser.add_argument('--interactive', action='store_true', default=True,
                       help='Use interactive mode (default)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found.")
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
    
    # Check how many already have trailers
    with_trailers = sum(1 for data in movie_data.values() if 'trailer_url' in data and data['trailer_url'])
    print(f"Movies with trailers: {with_trailers}")
    print(f"Movies without trailers: {len(movie_data) - with_trailers}")
    
    if args.urls:
        # Batch mode
        batch_url_adder(movie_data, args.urls, args.output)
    else:
        # Interactive mode
        interactive_trailer_adder(movie_data, args.output)

if __name__ == "__main__":
    main()
