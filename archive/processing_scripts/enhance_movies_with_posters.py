#!/usr/bin/env python3
"""
Enhance existing movie data with poster URLs from TMDB.
This script adds poster URLs to movies that already have tmdb_id.
"""

import json
import os
import time
import requests
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

def load_env_from_dotenv(dotenv_path: str = ".env") -> None:
    """Load environment variables from .env file"""
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v

def get_tmdb_poster_url(tmdb_id: int, api_key: str, size: str = "w500") -> Optional[str]:
    """
    Get poster URL for a movie from TMDB.
    
    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key
        size: Image size (w92, w154, w185, w342, w500, w780, original)
    
    Returns:
        Poster URL or None if not found
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/{size}{poster_path}"
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching poster for TMDB ID {tmdb_id}: {e}")
        return None

def enhance_movies_with_posters(input_file: str, output_file: str, api_key: str, 
                               size: str = "w500", batch_size: int = 50) -> Dict[str, Any]:
    """
    Enhance movie data with poster URLs.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        api_key: TMDB API key
        size: Poster image size
        batch_size: Number of movies to process in each batch
    
    Returns:
        Statistics about the enhancement process
    """
    # Load existing movie data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movies = data.get('movies', [])
    total_movies = len(movies)
    
    print(f"Processing {total_movies} movies...")
    
    # Statistics
    stats = {
        'total_movies': total_movies,
        'movies_with_tmdb_id': 0,
        'posters_found': 0,
        'posters_missing': 0,
        'errors': 0
    }
    
    # Process movies in batches
    for i in range(0, total_movies, batch_size):
        batch = movies[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(total_movies + batch_size - 1)//batch_size} "
              f"({i+1}-{min(i+batch_size, total_movies)})")
        
        for movie in batch:
            tmdb_id = movie.get('tmdb_id')
            
            if not tmdb_id:
                continue
                
            stats['movies_with_tmdb_id'] += 1
            
            # Skip if poster already exists
            if movie.get('poster_url'):
                continue
            
            # Get poster URL
            poster_url = get_tmdb_poster_url(tmdb_id, api_key, size)
            
            if poster_url:
                movie['poster_url'] = poster_url
                stats['posters_found'] += 1
            else:
                stats['posters_missing'] += 1
            
            # Rate limiting
            time.sleep(0.25)
        
        # Save progress after each batch
        if i + batch_size < total_movies:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Progress saved: {stats['posters_found']} posters found so far")
    
    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Enhance movie data with poster URLs")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    parser.add_argument("--size", default="w500", 
                       choices=["w92", "w154", "w185", "w342", "w500", "w780", "original"],
                       help="Poster image size")
    parser.add_argument("--batch-size", type=int, default=50, 
                       help="Number of movies to process in each batch")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_from_dotenv()
    
    # Get API key
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        print("Error: TMDB_API_KEY not found in environment variables")
        print("Please set TMDB_API_KEY in your .env file or environment")
        return 1
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    print(f"Enhancing movies with poster URLs...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Poster size: {args.size}")
    print(f"Batch size: {args.batch_size}")
    print()
    
    # Enhance movies
    stats = enhance_movies_with_posters(
        args.input, 
        args.output, 
        api_key, 
        args.size, 
        args.batch_size
    )
    
    # Print statistics
    print("\n" + "="*50)
    print("ENHANCEMENT COMPLETE")
    print("="*50)
    print(f"Total movies: {stats['total_movies']}")
    print(f"Movies with TMDB ID: {stats['movies_with_tmdb_id']}")
    print(f"Posters found: {stats['posters_found']}")
    print(f"Posters missing: {stats['posters_missing']}")
    print(f"Success rate: {stats['posters_found']/stats['movies_with_tmdb_id']*100:.1f}%" if stats['movies_with_tmdb_id'] > 0 else "N/A")
    print(f"Output saved to: {args.output}")
    
    return 0

if __name__ == "__main__":
    exit(main())
