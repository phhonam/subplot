#!/usr/bin/env python3
"""
Test script to verify poster URL fetching works correctly.
"""

import json
import os
import requests
from enhance_movies_with_posters import get_tmdb_poster_url, load_env_from_dotenv

def test_poster_fetching():
    """Test poster URL fetching with sample movies"""
    
    # Load environment
    load_env_from_dotenv()
    api_key = os.environ.get("TMDB_API_KEY")
    
    if not api_key:
        print("❌ TMDB_API_KEY not found in environment")
        return False
    
    # Test movies with known TMDB IDs
    test_movies = [
        {"title": "The Godfather", "tmdb_id": 238, "imdb_id": "tt0068646"},
        {"title": "Citizen Kane", "tmdb_id": 15, "imdb_id": "tt0033467"},
        {"title": "Casablanca", "tmdb_id": 289, "imdb_id": "tt0034583"},
        {"title": "The Matrix", "tmdb_id": 603, "imdb_id": "tt0133093"},
        {"title": "Pulp Fiction", "tmdb_id": 680, "imdb_id": "tt0110912"}
    ]
    
    print("🧪 Testing poster URL fetching...")
    print("=" * 50)
    
    success_count = 0
    
    for movie in test_movies:
        print(f"\n🎬 Testing: {movie['title']} (TMDB ID: {movie['tmdb_id']})")
        
        # Test different sizes
        sizes = ["w92", "w185", "w500", "original"]
        
        for size in sizes:
            poster_url = get_tmdb_poster_url(movie['tmdb_id'], api_key, size)
            
            if poster_url:
                print(f"  ✅ {size}: {poster_url}")
                
                # Test if URL is accessible
                try:
                    response = requests.head(poster_url, timeout=5)
                    if response.status_code == 200:
                        print(f"     📷 Image accessible ({response.headers.get('content-type', 'unknown type')})")
                    else:
                        print(f"     ⚠️  Image not accessible (status: {response.status_code})")
                except requests.RequestException as e:
                    print(f"     ❌ Error checking image: {e}")
            else:
                print(f"  ❌ {size}: No poster found")
        
        if any(get_tmdb_poster_url(movie['tmdb_id'], api_key, size) for size in sizes):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{len(test_movies)} movies have posters")
    
    if success_count == len(test_movies):
        print("🎉 All tests passed! Poster fetching is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check your API key and network connection.")
        return False

def test_with_actual_data():
    """Test with a few movies from your actual dataset"""
    
    # Load a small sample from your merged data
    try:
        with open('/Users/nam/movie-recommender/merged_movie_data.json', 'r') as f:
            data = json.load(f)
        
        movies = data.get('movies', [])[:5]  # Test first 5 movies
        
        print(f"\n🎯 Testing with {len(movies)} movies from your dataset...")
        print("=" * 50)
        
        load_env_from_dotenv()
        api_key = os.environ.get("TMDB_API_KEY")
        
        if not api_key:
            print("❌ TMDB_API_KEY not found")
            return False
        
        for movie in movies:
            title = movie.get('title', 'Unknown')
            tmdb_id = movie.get('tmdb_id')
            
            if not tmdb_id:
                print(f"❌ {title}: No TMDB ID")
                continue
            
            poster_url = get_tmdb_poster_url(tmdb_id, api_key, "w500")
            
            if poster_url:
                print(f"✅ {title}: {poster_url}")
            else:
                print(f"❌ {title}: No poster found")
        
        return True
        
    except FileNotFoundError:
        print("❌ merged_movie_data.json not found")
        return False
    except Exception as e:
        print(f"❌ Error testing with actual data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting poster fetching tests...")
    
    # Test with known movies
    test1_passed = test_poster_fetching()
    
    # Test with actual data
    test2_passed = test_with_actual_data()
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! You're ready to enhance your movie data with posters.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above before proceeding.")
