#!/usr/bin/env python3
"""
Demo script showing how poster URLs work with your movie data.
"""

import json
import os
from enhance_movies_with_posters import get_tmdb_poster_url, load_env_from_dotenv

def demo_poster_integration():
    """Demonstrate poster URL integration"""
    
    print("🎬 Movie Poster Integration Demo")
    print("=" * 50)
    
    # Load environment
    load_env_from_dotenv()
    api_key = os.environ.get("TMDB_API_KEY")
    
    if not api_key:
        print("❌ TMDB_API_KEY not found in environment")
        print("Please set your TMDB API key in .env file")
        return
    
    # Sample movies from your dataset
    sample_movies = [
        {"title": "The Godfather", "tmdb_id": 238, "year": "1972"},
        {"title": "Citizen Kane", "tmdb_id": 15, "year": "1941"},
        {"title": "Casablanca", "tmdb_id": 289, "year": "1943"},
        {"title": "The Matrix", "tmdb_id": 603, "year": "1999"},
        {"title": "Pulp Fiction", "tmdb_id": 680, "year": "1994"}
    ]
    
    print(f"📋 Testing poster URLs for {len(sample_movies)} sample movies:")
    print()
    
    enhanced_movies = []
    
    for movie in sample_movies:
        print(f"🎭 {movie['title']} ({movie['year']})")
        print(f"   TMDB ID: {movie['tmdb_id']}")
        
        # Get poster URL
        poster_url = get_tmdb_poster_url(movie['tmdb_id'], api_key, "w500")
        
        if poster_url:
            print(f"   ✅ Poster: {poster_url}")
            
            # Create enhanced movie object
            enhanced_movie = {
                "title": movie['title'],
                "year": movie['year'],
                "tmdb_id": movie['tmdb_id'],
                "poster_url": poster_url,
                "director": "Unknown",  # Would be filled by full data
                "genre_tags": [],       # Would be filled by full data
                "plot_summary": ""      # Would be filled by full data
            }
            enhanced_movies.append(enhanced_movie)
        else:
            print(f"   ❌ No poster found")
        
        print()
    
    # Show JSON structure
    print("📄 Enhanced Movie Data Structure:")
    print("=" * 50)
    if enhanced_movies:
        sample_enhanced = enhanced_movies[0]
        print(json.dumps(sample_enhanced, indent=2))
    
    print()
    print("🚀 Next Steps:")
    print("1. Run: python test_poster_fetching.py")
    print("2. Run: python enhance_movies_with_posters.py --input merged_movie_data.json --output enhanced_data.json")
    print("3. Update your frontend to display poster images")
    print()
    print("📖 See POSTER_INTEGRATION_GUIDE.md for complete instructions")

if __name__ == "__main__":
    demo_poster_integration()
