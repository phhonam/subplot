#!/usr/bin/env python3
"""
Convert merged_movie_data_with_images.json to the format expected by the app.
The app expects: {title: {movie_data}}
But we have: {movies: [{movie_data}]}
"""

import json
import sys

def convert_enhanced_data(input_file, output_file):
    """Convert enhanced data to app-compatible format"""
    
    # Load the enhanced data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movies = data.get('movies', [])
    
    # Convert to title-keyed format
    converted = {}
    for movie in movies:
        title = movie.get('title', '')
        if title:
            converted[title] = movie
    
    # Save the converted data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(converted)} movies from {input_file} to {output_file}")
    return len(converted)

if __name__ == "__main__":
    input_file = "merged_movie_data_with_images.json"
    output_file = "movie_profiles_with_images.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    count = convert_enhanced_data(input_file, output_file)
    print(f"🎬 Ready to use {output_file} with {count} movies including backdrop URLs!")
