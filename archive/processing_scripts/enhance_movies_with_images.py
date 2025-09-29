#!/usr/bin/env python3
"""
Enhance existing movie data with poster and backdrop URLs from TMDB.
This script adds both poster_url and backdrop_url to movies that have tmdb_id.
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

def get_tmdb_images(tmdb_id: int, api_key: str) -> Dict[str, Optional[str]]:
    """
    Get poster and backdrop URLs for a movie from TMDB.
    
    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key
    
    Returns:
        Dictionary with poster_url and backdrop_url
    """
    # Get basic movie data for poster
    movie_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    images_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
    params = {"api_key": api_key}
    
    result = {
        "poster_url": None,
        "backdrop_url": None
    }
    
    try:
        # Get movie details for poster
        response = requests.get(movie_url, params=params, timeout=10)
        response.raise_for_status()
        movie_data = response.json()
        
        poster_path = movie_data.get("poster_path")
        if poster_path:
            result["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Get images for backdrops
        response = requests.get(images_url, params=params, timeout=10)
        response.raise_for_status()
        images_data = response.json()
        
        # Get the best backdrop (highest rated)
        backdrops = images_data.get("backdrops", [])
        if backdrops:
            # Sort by vote_average (descending) and take the best one
            best_backdrop = max(backdrops, key=lambda x: x.get("vote_average", 0))
            backdrop_path = best_backdrop.get("file_path")
            if backdrop_path:
                result["backdrop_url"] = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
        
        return result
        
    except requests.RequestException as e:
        print(f"Error fetching images for TMDB ID {tmdb_id}: {e}")
        return result

def enhance_movies_with_images(input_file: str, output_file: str, api_key: str, 
                              batch_size: int = 50) -> Dict[str, Any]:
    """
    Enhance movie data with poster and backdrop URLs.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        api_key: TMDB API key
        batch_size: Number of movies to process in each batch
    
    Returns:
        Statistics about the enhancement process
    """
    # Load existing movie data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movies = data.get('movies', [])
    total_movies = len(movies)
    
    print(f"Processing {total_movies} movies for posters and backdrops...")
    
    # Statistics
    stats = {
        'total_movies': total_movies,
        'movies_with_tmdb_id': 0,
        'posters_found': 0,
        'backdrops_found': 0,
        'both_found': 0,
        'errors': 0
    }
    
    # Process movies in batches
    for i in range(0, total_movies, batch_size):
        batch = movies[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (total_movies + batch_size - 1)//batch_size
        
        print(f"\n🎬 Processing batch {batch_num}/{total_batches} "
              f"({i+1}-{min(i+batch_size, total_movies)})")
        
        for j, movie in enumerate(batch):
            tmdb_id = movie.get('tmdb_id')
            
            if not tmdb_id:
                continue
                
            stats['movies_with_tmdb_id'] += 1
            
            # Skip if both images already exist
            if movie.get('poster_url') and movie.get('backdrop_url'):
                stats['posters_found'] += 1
                stats['backdrops_found'] += 1
                stats['both_found'] += 1
                continue
            
            # Show progress for every 10th movie in batch
            if (j + 1) % 10 == 0 or j == 0:
                print(f"  Processing: {movie.get('title', 'Unknown')} (TMDB: {tmdb_id})")
            
            # Get images
            images = get_tmdb_images(tmdb_id, api_key)
            
            # Update movie data
            if images['poster_url'] and not movie.get('poster_url'):
                movie['poster_url'] = images['poster_url']
                stats['posters_found'] += 1
            elif movie.get('poster_url'):
                stats['posters_found'] += 1
                
            if images['backdrop_url'] and not movie.get('backdrop_url'):
                movie['backdrop_url'] = images['backdrop_url']
                stats['backdrops_found'] += 1
            elif movie.get('backdrop_url'):
                stats['backdrops_found'] += 1
            
            if movie.get('poster_url') and movie.get('backdrop_url'):
                stats['both_found'] += 1
            
            # Rate limiting
            time.sleep(0.25)
        
        # Save progress after each batch
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Batch {batch_num} complete: {stats['posters_found']} posters, {stats['backdrops_found']} backdrops")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description="Enhance movie data with poster and backdrop URLs")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    parser.add_argument("--batch-size", type=int, default=50, 
                       help="Number of movies to process in each batch")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_from_dotenv()
    
    # Get API key
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        print("❌ Error: TMDB_API_KEY not found in environment variables")
        print("Please set TMDB_API_KEY in your .env file or environment")
        return 1
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file '{args.input}' not found")
        return 1
    
    print("🎬 Movie Image Enhancement")
    print("=" * 50)
    print(f"📁 Input: {args.input}")
    print(f"📁 Output: {args.output}")
    print(f"📦 Batch size: {args.batch_size}")
    print(f"⏱️  Estimated time: ~15-20 minutes for 1,204 movies")
    print()
    
    # Enhance movies
    start_time = time.time()
    stats = enhance_movies_with_images(
        args.input, 
        args.output, 
        api_key, 
        args.batch_size
    )
    end_time = time.time()
    
    # Print statistics
    print("\n" + "=" * 50)
    print("🎉 ENHANCEMENT COMPLETE")
    print("=" * 50)
    print(f"⏱️  Total time: {end_time - start_time:.1f} seconds")
    print(f"📊 Total movies: {stats['total_movies']}")
    print(f"🎯 Movies with TMDB ID: {stats['movies_with_tmdb_id']}")
    print(f"🖼️  Posters found: {stats['posters_found']}")
    print(f"🎬 Backdrops found: {stats['backdrops_found']}")
    print(f"✨ Movies with both: {stats['both_found']}")
    
    if stats['movies_with_tmdb_id'] > 0:
        poster_rate = stats['posters_found']/stats['movies_with_tmdb_id']*100
        backdrop_rate = stats['backdrops_found']/stats['movies_with_tmdb_id']*100
        both_rate = stats['both_found']/stats['movies_with_tmdb_id']*100
        print(f"📈 Poster success rate: {poster_rate:.1f}%")
        print(f"📈 Backdrop success rate: {backdrop_rate:.1f}%")
        print(f"📈 Both images rate: {both_rate:.1f}%")
    
    print(f"💾 Output saved to: {args.output}")
    print("\n🚀 Next steps:")
    print("1. Update your frontend to display poster and backdrop images")
    print("2. Use poster_url for card thumbnails")
    print("3. Use backdrop_url for hero images and scene previews")
    
    return 0

if __name__ == "__main__":
    exit(main())
