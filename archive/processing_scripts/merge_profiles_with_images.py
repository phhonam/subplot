#!/usr/bin/env python3
"""
Merge movie profiles with image data to create a complete dataset.
"""

import json
import sys

def merge_profiles_with_images(profiles_file, images_file, output_file):
    """Merge movie profiles with image data"""
    
    # Load movie profiles (rich data)
    with open(profiles_file, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    # Load image data (basic data with images)
    with open(images_file, 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Merge the data
    merged = {}
    for title, profile_data in profiles.items():
        # Start with the rich profile data
        merged[title] = profile_data.copy()
        
        # Add image data if available
        if title in images_data:
            image_data = images_data[title]
            merged[title]['poster_url'] = image_data.get('poster_url', '')
            merged[title]['backdrop_url'] = image_data.get('backdrop_url', '')
            merged[title]['tmdb_id'] = image_data.get('tmdb_id')
            merged[title]['imdb_id'] = image_data.get('imdb_id')
            merged[title]['plot_summary'] = image_data.get('plot_summary', '')
            merged[title]['genre_tags'] = image_data.get('genre_tags', [])
    
    # Save the merged data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Merged {len(merged)} movies from profiles and images")
    return len(merged)

if __name__ == "__main__":
    profiles_file = "movie_profiles_merged.json"
    images_file = "movie_profiles_with_images.json"
    output_file = "movie_profiles_complete.json"
    
    if len(sys.argv) > 1:
        profiles_file = sys.argv[1]
    if len(sys.argv) > 2:
        images_file = sys.argv[2]
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    
    count = merge_profiles_with_images(profiles_file, images_file, output_file)
    print(f"🎬 Complete dataset with {count} movies including profiles and images!")
