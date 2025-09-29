#!/usr/bin/env python3
"""
Merge image data from merged_movie_data_with_images.json into movie_profiles_merged.json
This creates a single complete dataset with both profile data and image URLs.
"""

import json
from pathlib import Path

def normalize_title(title):
    """Normalize title for matching (same logic as frontend)"""
    return str(title or '').lower().strip()

def merge_image_data():
    """Merge image data into movie profiles"""
    
    # Load the profile data
    print("📁 Loading movie_profiles_merged.json...")
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles_data = json.load(f)
    
    # Load the image data
    print("📁 Loading merged_movie_data_with_images.json...")
    with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Create a lookup map for image data by normalized title
    image_lookup = {}
    for movie in images_data.get('movies', []):
        title = movie.get('title', '')
        if title:
            key = normalize_title(title)
            image_lookup[key] = {
                'poster_url': movie.get('poster_url', ''),
                'backdrop_url': movie.get('backdrop_url', ''),
                'director': movie.get('director', ''),
                'year': movie.get('year', ''),
                'imdb_id': movie.get('imdb_id', ''),
                'tmdb_id': movie.get('tmdb_id', ''),
                'genre_tags': movie.get('genre_tags', []),
                'plot_summary': movie.get('plot_summary', '')
            }
    
    print(f"📊 Found {len(image_lookup)} movies with image data")
    
    # Merge the data
    merged_count = 0
    missing_count = 0
    
    for title, profile in profiles_data.items():
        key = normalize_title(title)
        image_info = image_lookup.get(key)
        
        if image_info:
            # Merge image data into profile
            profile['poster_url'] = image_info['poster_url']
            profile['backdrop_url'] = image_info['backdrop_url']
            
            # Also merge other useful metadata if not already present
            if not profile.get('director') and image_info['director']:
                profile['director'] = image_info['director']
            if not profile.get('year') and image_info['year']:
                profile['year'] = image_info['year']
            if not profile.get('imdb_id') and image_info['imdb_id']:
                profile['imdb_id'] = image_info['imdb_id']
            if not profile.get('tmdb_id') and image_info['tmdb_id']:
                profile['tmdb_id'] = image_info['tmdb_id']
            if not profile.get('genre_tags') and image_info['genre_tags']:
                profile['genre_tags'] = image_info['genre_tags']
            if not profile.get('plot_summary') and image_info['plot_summary']:
                profile['plot_summary'] = image_info['plot_summary']
            
            merged_count += 1
        else:
            missing_count += 1
            print(f"⚠️  No image data found for: {title}")
    
    print(f"✅ Successfully merged image data for {merged_count} movies")
    print(f"❌ Missing image data for {missing_count} movies")
    
    # Save the merged data
    print("💾 Saving merged data to movie_profiles_merged.json...")
    with open('movie_profiles_merged.json', 'w', encoding='utf-8') as f:
        json.dump(profiles_data, f, indent=2, ensure_ascii=False)
    
    print("🎉 Merge complete! movie_profiles_merged.json now contains image data")
    
    # Show some sample data
    print("\n📋 Sample merged data:")
    sample_title = list(profiles_data.keys())[0]
    sample_profile = profiles_data[sample_title]
    print(f"Title: {sample_title}")
    print(f"Poster URL: {sample_profile.get('poster_url', 'None')}")
    print(f"Backdrop URL: {sample_profile.get('backdrop_url', 'None')}")
    print(f"Director: {sample_profile.get('director', 'None')}")
    print(f"Year: {sample_profile.get('year', 'None')}")

if __name__ == "__main__":
    merge_image_data()
