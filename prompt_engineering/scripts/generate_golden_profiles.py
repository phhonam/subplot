#!/usr/bin/env python3
"""
Extract profile_text from existing movie_profiles_merged.json for golden dataset movies.
This gives us the baseline (v1.0) profile_text for comparison.
"""

import json
from pathlib import Path

def extract_profile_text(movies_list, input_file='movie_profiles_merged.json', output_dir='prompt_engineering/golden_dataset'):
    """Extract profile_text for specific movies from merged profiles"""
    
    # Load all movie profiles
    with open(input_file, 'r', encoding='utf-8') as f:
        all_profiles = json.load(f)
    
    # Extract profiles for golden dataset movies
    golden_profiles = {}
    
    for movie_title in movies_list:
        if movie_title in all_profiles:
            movie_data = all_profiles[movie_title]
            golden_profiles[movie_title] = {
                'title': movie_data.get('title', movie_title),
                'year': movie_data.get('year', ''),
                'director': movie_data.get('director', ''),
                'genres': movie_data.get('genre_tags', []),
                'plot_summary': movie_data.get('plot_summary', ''),
                'profile_text': movie_data.get('profile_text', ''),
                'version': 'v1.0',
                'generated_at': '2025-10-18'
            }
            print(f"✅ Extracted: {movie_title}")
        else:
            print(f"❌ Not found: {movie_title}")
    
    # Save to file
    output_file = Path(output_dir) / 'generated_profiles_v1.0.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(golden_profiles, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(golden_profiles)} profiles to {output_file}")
    return golden_profiles

if __name__ == "__main__":
    # Select 5 movies from golden dataset
    golden_movies = [
        'Citizen Kane',
        'Tangerine', 
        'Close-Up',
        'Bicycle Thieves',
        'In the Mood for Love'
    ]
    
    extract_profile_text(golden_movies)
