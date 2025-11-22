#!/usr/bin/env python3
"""
Generate profile_text for golden dataset movies using current movie_profiles_merged.json
"""

import json
import sys
from pathlib import Path

def load_golden_dataset():
    """Load the golden dataset movies"""
    golden_dataset_path = Path("/Users/nam/movie-recommender/prompt_engineering/golden_dataset/movies.json")
    
    with open(golden_dataset_path, 'r') as f:
        data = json.load(f)
    
    return data["golden_dataset"]["movies"]

def load_movie_profiles():
    """Load the current movie profiles"""
    profiles_path = Path("/Users/nam/movie-recommender/movie_profiles_merged.json")
    
    with open(profiles_path, 'r') as f:
        profiles = json.load(f)
    
    return profiles

def extract_profile_texts(golden_movies, movie_profiles):
    """Extract profile_text for golden dataset movies"""
    
    results = {}
    missing_movies = []
    
    for movie in golden_movies:
        title = movie["title"]
        
        if title in movie_profiles:
            profile = movie_profiles[title]
            results[title] = {
                "profile_text": profile.get("profile_text", ""),
                "version": "v1.0_baseline",
                "generated_at": "2025-10-18",
                "movie_info": {
                    "year": movie["year"],
                    "director": movie["director"],
                    "country": movie["country"],
                    "category": movie["category"],
                    "key_challenges": movie["key_challenges"]
                }
            }
        else:
            missing_movies.append(title)
    
    return results, missing_movies

def save_results(results, missing_movies, version="v1.0"):
    """Save the extracted profile_texts"""
    
    output_path = Path(f"/Users/nam/movie-recommender/prompt_engineering/golden_dataset/generated_profiles_{version}.json")
    
    output_data = {
        "version": version,
        "extraction_date": "2025-10-18",
        "total_movies": len(results),
        "missing_movies": missing_movies,
        "profiles": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Extracted {len(results)} profile_texts to {output_path}")
    
    if missing_movies:
        print(f"⚠️  Missing movies: {missing_movies}")
    
    return output_path

def main():
    """Main function"""
    print("🎬 Extracting profile_text for golden dataset...")
    
    # Load golden dataset
    golden_movies = load_golden_dataset()
    print(f"📋 Loaded {len(golden_movies)} movies from golden dataset")
    
    # Load current movie profiles
    movie_profiles = load_movie_profiles()
    print(f"📚 Loaded {len(movie_profiles)} movie profiles")
    
    # Extract profile_texts
    results, missing_movies = extract_profile_texts(golden_movies, movie_profiles)
    
    # Save results
    output_path = save_results(results, missing_movies)
    
    print(f"🎯 Profile extraction complete!")
    print(f"   - Found profiles: {len(results)}")
    print(f"   - Missing movies: {len(missing_movies)}")
    print(f"   - Output: {output_path}")

if __name__ == "__main__":
    main()
