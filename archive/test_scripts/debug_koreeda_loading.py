#!/usr/bin/env python3
"""
Debug script to check Koreeda movies data consistency
"""

import json

def debug_koreeda_data():
    print("🔍 Debugging Koreeda movies data...")
    
    # Load movie_profiles_merged.json
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    # Load merged_movie_data_with_images.json
    with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Find Koreeda movies in profiles
    koreeda_profiles = {}
    for title, profile in profiles.items():
        if profile.get('director') == 'Hirokazu Kore-eda':
            koreeda_profiles[title] = profile
    
    print(f"📊 Found {len(koreeda_profiles)} Kore-eda movies in profiles:")
    for title in sorted(koreeda_profiles.keys()):
        profile = koreeda_profiles[title]
        print(f"   - {title} ({profile.get('year', 'N/A')})")
        print(f"     Director: {profile.get('director', 'N/A')}")
        print(f"     Poster: {profile.get('poster_url', 'N/A')}")
        print(f"     IMDB: {profile.get('imdb_id', 'N/A')}")
        print(f"     TMDB: {profile.get('tmdb_id', 'N/A')}")
        print()
    
    # Check if they exist in images data
    images_movies = {movie['title']: movie for movie in images_data['movies']}
    
    print("🔍 Checking if Koreeda movies exist in merged_movie_data_with_images.json:")
    for title in sorted(koreeda_profiles.keys()):
        if title in images_movies:
            movie = images_movies[title]
            print(f"   ✅ {title} - Found in images data")
            print(f"      Director: {movie.get('director', 'N/A')}")
            print(f"      Poster: {movie.get('poster_url', 'N/A')}")
            print(f"      IMDB: {movie.get('imdb_id', 'N/A')}")
            print(f"      TMDB: {movie.get('tmdb_id', 'N/A')}")
        else:
            print(f"   ❌ {title} - NOT found in images data")
        print()
    
    # Check for data inconsistencies
    print("🔍 Checking for data inconsistencies:")
    for title in sorted(koreeda_profiles.keys()):
        if title in images_movies:
            profile = koreeda_profiles[title]
            movie = images_movies[title]
            
            inconsistencies = []
            if profile.get('director') != movie.get('director'):
                inconsistencies.append(f"Director: profile='{profile.get('director')}' vs movie='{movie.get('director')}'")
            if profile.get('year') != movie.get('year'):
                inconsistencies.append(f"Year: profile='{profile.get('year')}' vs movie='{movie.get('year')}'")
            if profile.get('poster_url') != movie.get('poster_url'):
                inconsistencies.append(f"Poster: profile='{profile.get('poster_url')}' vs movie='{movie.get('poster_url')}'")
            if profile.get('imdb_id') != movie.get('imdb_id'):
                inconsistencies.append(f"IMDB: profile='{profile.get('imdb_id')}' vs movie='{movie.get('imdb_id')}'")
            if profile.get('tmdb_id') != movie.get('tmdb_id'):
                inconsistencies.append(f"TMDB: profile='{profile.get('tmdb_id')}' vs movie='{movie.get('tmdb_id')}'")
            
            if inconsistencies:
                print(f"   ⚠️  {title} has inconsistencies:")
                for inc in inconsistencies:
                    print(f"      - {inc}")
            else:
                print(f"   ✅ {title} - Data is consistent")
        print()

if __name__ == "__main__":
    debug_koreeda_data()
