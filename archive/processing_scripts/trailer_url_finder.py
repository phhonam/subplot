#!/usr/bin/env python3
"""
Trailer URL Finder

This script helps you find YouTube trailer URLs for your movies by:
1. Opening YouTube search pages for each movie
2. Providing a simple interface to copy-paste URLs
3. Generating a batch file for easy import

Usage:
    python trailer_url_finder.py --input movie_profiles_merged.json --limit 10
"""

import json
import argparse
import webbrowser
import time
from pathlib import Path
from typing import Dict, Any, List
import re

def extract_year_from_title(title: str) -> int:
    """Extract year from movie title if present"""
    year_match = re.search(r'\((\d{4})\)$', title)
    if year_match:
        return int(year_match.group(1))
    
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if year_match:
        return int(year_match.group(0))
    
    return None

def build_youtube_search_url(movie_title: str, year: int = None) -> str:
    """Build YouTube search URL for a movie"""
    query_parts = [movie_title]
    if year:
        query_parts.append(str(year))
    query_parts.append("trailer")
    
    query = " ".join(query_parts)
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def generate_trailer_urls_file(movies: List[tuple], output_file: str):
    """Generate a template file for trailer URLs"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Trailer URLs for Movies\n")
        f.write("# Format: Movie Title: YouTube URL\n")
        f.write("# Example: The Godfather: https://www.youtube.com/watch?v=sY1S34973zA\n\n")
        
        for title, data in movies:
            year = extract_year_from_title(title)
            year_str = f" ({year})" if year else ""
            f.write(f"{title}{year_str}:\n")
    
    print(f"Generated template file: {output_file}")
    print("Edit this file to add YouTube URLs, then use:")
    print(f"python manual_trailer_adder.py --input movie_profiles_merged.json --urls {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Find YouTube trailer URLs for movies')
    parser.add_argument('--input', '-i', default='movie_profiles_merged.json', 
                       help='Input movie data file')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of movies to process')
    parser.add_argument('--start', type=int, default=0, help='Start from this movie index')
    parser.add_argument('--generate-template', action='store_true', 
                       help='Generate a template file for manual URL entry')
    parser.add_argument('--template-file', default='trailer_urls.txt',
                       help='Template file name (default: trailer_urls.txt)')
    parser.add_argument('--delay', type=float, default=2.0, 
                       help='Delay between opening browser tabs (seconds)')
    
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
    
    # Get movies to process
    movies = list(movie_data.items())
    if args.limit:
        movies = movies[args.start:args.start + args.limit]
    else:
        movies = movies[args.start:]
    
    # Filter out movies that already have trailers
    movies_without_trailers = []
    for title, data in movies:
        if 'trailer_url' not in data or not data['trailer_url']:
            movies_without_trailers.append((title, data))
    
    print(f"Movies without trailers: {len(movies_without_trailers)}")
    
    if args.generate_template:
        generate_trailer_urls_file(movies_without_trailers, args.template_file)
        return
    
    if not movies_without_trailers:
        print("All selected movies already have trailers!")
        return
    
    print(f"\nOpening YouTube search pages for {len(movies_without_trailers)} movies...")
    print("Press Ctrl+C to stop")
    
    try:
        for i, (title, data) in enumerate(movies_without_trailers):
            year = extract_year_from_title(title)
            search_url = build_youtube_search_url(title, year)
            
            print(f"[{i+1}/{len(movies_without_trailers)}] Opening: {title}")
            print(f"  Search URL: {search_url}")
            
            # Open in browser
            webbrowser.open(search_url)
            
            # Wait before opening next tab
            if i < len(movies_without_trailers) - 1:
                time.sleep(args.delay)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    print(f"\nOpened {min(i+1, len(movies_without_trailers))} search pages")
    print("\nNext steps:")
    print("1. Find trailer URLs from the opened YouTube pages")
    print("2. Copy the URLs")
    print("3. Use the manual trailer adder to add them:")
    print("   python manual_trailer_adder.py --input movie_profiles_merged.json")
    print("\nOr generate a template file for batch processing:")
    print(f"   python trailer_url_finder.py --input {args.input} --generate-template")

if __name__ == "__main__":
    main()
